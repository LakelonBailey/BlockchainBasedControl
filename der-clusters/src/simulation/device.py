import asyncio
import json
import websockets
import argparse
import random
from datetime import datetime
from src.utils.devices import get_device_name_map
import pytz


async def send_energy_data(device_name: str, meter_origin: str):
    """
    Connects to the smart meter and sends energy updates at random intervals from 1-10
    seconds.
    """

    device_name_map = get_device_name_map()
    device = device_name_map[device_name]()
    device_id = device.id
    ws_url = f"{meter_origin}/ws/{device_id}"
    start_time = datetime.now(pytz.UTC)
    try:
        async with websockets.connect(ws_url) as websocket:
            while True:
                current_time = datetime.now(pytz.UTC)
                energy_kwh = device.calculate_kwh(start_time, current_time)
                message = {
                    "timestamp": current_time.isoformat(),
                    "energy_kwh": energy_kwh,
                    "device": device.to_dict(),
                }
                start_time = current_time

                await websocket.send(json.dumps(message))
                print(f"[{device_id}] Sent: {message}")

                await asyncio.sleep(random.randint(1, 10))
    except Exception as e:
        print(f"[{device_id}] Connection error: {e}")
        await asyncio.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulated DER device daemon.")
    parser.add_argument(
        "--device",
        required=True,
        help=f"Device type. Options: {','.join(get_device_name_map().keys())}",
    )
    parser.add_argument(
        "--meter-origin",
        required=True,
        help="Smart meter WebSocket URL",
    )

    args = parser.parse_args()

    asyncio.run(send_energy_data(args.device, args.meter_origin))
