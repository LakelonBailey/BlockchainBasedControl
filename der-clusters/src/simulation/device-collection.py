import argparse
import multiprocessing
import os
import time
import random
from src.utils.devices import get_device_name_map


def run_device_cmd(device_name: str, meter_origin: str):
    nodes = []
    """
    Top-level function that will be used as the target in multiprocessing.
    """
    os.system(
        f"python3 -m src.simulation.device --device {device_name} "
        f"--meter-origin {meter_origin}"
    )


def start_device(device_name: str, meter_origin: str):
    """
    Spawns a process that calls our top-level run_device_cmd function.
    """
    process = multiprocessing.Process(
        target=run_device_cmd,
        args=(device_name, meter_origin),
    )
    process.start()
    return process


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DER Cluster Manager")

    parser.add_argument(
        "--num-devices",
        type=int,
        required=True,
        help="Number of total devices to spawn",
    )
    parser.add_argument(
        "--consumption-production-ratio",
        type=str,
        default="50:50",
        help="Ratio of consumption to production devices, e.g. '60:40'. Default is \
'50:50'.",
    )
    parser.add_argument(
        "--meter-origin",
        type=str,
        default=os.environ.get("METER_ORIGIN", "ws://localhost:8000"),
        help="Smart meter WebSocket URL (e.g., ws://localhost:8000)",
    )

    args = parser.parse_args()

    # Parse ratio string (e.g., "50:50" -> "50", "50")
    try:
        cons_str, prod_str = args.consumption_production_ratio.split(":")
        cons_ratio = int(cons_str)
        prod_ratio = int(prod_str)
    except ValueError:
        raise ValueError(
            "Invalid format for --consumption-production-ratio: "
            f"{args.consumption_production_ratio}. "
            "Expected something like '50:50'."
        )

    # Calculate how many consumption vs production devices we need
    total_ratio = cons_ratio + prod_ratio
    num_consumption = round(args.num_devices * cons_ratio / total_ratio)
    num_production = args.num_devices - num_consumption  # remainder

    # Dynamically retrieve the device name -> class mappings
    consumption_map = get_device_name_map("consumption")
    production_map = get_device_name_map("production")

    # Extract just the names
    consumption_names = list(consumption_map.keys())
    production_names = list(production_map.keys())

    # Randomly pick device names
    chosen_consumption = random.choices(consumption_names, k=num_consumption)
    chosen_production = random.choices(production_names, k=num_production)

    # Merge into single list and shuffle
    device_names = chosen_consumption + chosen_production
    random.shuffle(device_names)

    print(
        f"Starting DER Cluster with {args.num_devices} devices "
        f"({num_consumption} consumption, {num_production} production)."
    )
    processes = []

    try:
        for device_name in device_names:
            process = start_device(device_name, args.meter_origin)
            processes.append(process)
            print(f"[{device_name}] Started with PID {process.pid}")
        
        # Keep running until user interrupts
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all device daemons...")
        for process in processes:
            print(f"Terminating PID {process.pid}")
            process.terminate()
            process.join()  # Ensure processes exit cleanly

        print("All devices stopped.")
