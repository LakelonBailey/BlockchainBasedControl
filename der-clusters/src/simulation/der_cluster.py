import argparse
import subprocess
import signal
import time
from src.utils.devices import get_device_name_map


def start_device(device_type, meter_origin):
    """Start a device daemon process."""
    commands = [
        "python",
        "-m",
        "src.simulation.device",
        "--device",
        device_type,
        "--meter-origin",
        meter_origin,
    ]
    process = subprocess.Popen(
        commands,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return process


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DER Cluster Manager")
    parser.add_argument(
        "--devices",
        type=str,
        required=True,
        help=f"Comma-separated list of device names. Options: \
            {', '.join(get_device_name_map().keys())}",
    )
    parser.add_argument(
        "--meter-origin",
        type=str,
        required=True,
        help="Smart meter WebSocket URL (e.g., ws://localhost:8000)",
    )

    args = parser.parse_args()
    device_types = args.devices.split(",")

    print("Starting DER Cluster...")
    processes = []

    try:
        for device in device_types:
            process = start_device(device, args.meter_origin)
            processes.append(process)
            print(f"[{device}] Started with PID {process.pid}")

        # Keep running until user interrupts
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping all device daemons...")
        for process in processes:
            print(f"[{device}] Terminating PID {process.pid}")
            process.send_signal(signal.SIGTERM)  # Graceful shutdown
            process.wait()  # Ensure process exits

        print("All devices stopped.")
