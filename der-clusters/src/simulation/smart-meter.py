import os
import json
import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.utils.server import CentralServerAPI

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

# Constant: number of transactions to buffer before a batch upload.
TRANSACTION_BUFFER_SIZE = 4

# Initialize FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


connected_devices = set()
transactions = []

# Create an async lock to protect the transactions list.
transaction_lock = asyncio.Lock()


@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for receiving energy data from devices."""
    await websocket.accept()
    connected_devices.add(device_id)
    logger.info(f"Device Connected | ID: {device_id}")
    server_api = CentralServerAPI(CLIENT_ID, CLIENT_SECRET, scope="transactions:upload")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            device_id = message["device"]["id"]
            energy_kwh = message["energy_kwh"]
            device_type = message["device"]["type"]

            batch = None
            async with transaction_lock:
                # TODO: Send timestamp as well. Don't let the server automatically add
                # a time stamp.
                transactions.append(
                    {"energy_kwh": energy_kwh, "transaction_type": device_type}
                )
                if len(transactions) >= TRANSACTION_BUFFER_SIZE:
                    batch = transactions.copy()
                    transactions.clear()

            if batch is not None:
                try:
                    await server_api.post_transactions(batch)
                    logger.info(f"Uploaded {len(batch)} transactions.")
                except Exception as e:
                    logger.error(f"Failed to post transactions: {e}")

            # Log each energy transaction.
            logger.info(
                f"Energy Transaction | ID: {device_id} | Type: {device_type} | kWh: "
                f"{energy_kwh:.8f}"
            )

    except WebSocketDisconnect:
        connected_devices.remove(device_id)
        logger.info(f"Device Disconnected | ID: {device_id}")


@app.get("/devices")
async def get_connected_devices():
    """Retrieve the latest connected devices."""
    return list(connected_devices)
