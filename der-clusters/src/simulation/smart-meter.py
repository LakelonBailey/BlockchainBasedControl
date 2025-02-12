import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Store connected devices
connected_devices = set()


@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for receiving energy data from devices."""
    await websocket.accept()
    connected_devices.add(device_id)
    logger.info(f"Device Connected | ID: {device_id}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Extract relevant fields
            device_id = message["device"]["id"]
            energy_kwh = message["energy_kwh"]
            device_type = message["device"]["type"]  # 'consumption' or 'production'

            # Log the energy transaction
            logger.info(
                f"Energy Transaction | ID: {device_id} | Type: {device_type} | "
                f"kWh: {energy_kwh:.8f}"
            )

    except WebSocketDisconnect:
        connected_devices.remove(device_id)
        logger.info(f"Device Disconnected | ID: {device_id}")


@app.get("/devices")
async def get_connected_devices():
    """Retrieve the latest connected devices."""
    return list(connected_devices)
