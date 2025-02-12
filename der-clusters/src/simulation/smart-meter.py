from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
from pprint import pprint

app = FastAPI()

# Store connected devices and their data
connected_devices = {}


@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """WebSocket endpoint for receiving energy data from devices."""
    await websocket.accept()
    connected_devices[device_id] = websocket
    print(f"[{device_id}] Connected.")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print("\nMESSAGE RECEIVED:")
            pprint(message)

    except WebSocketDisconnect:
        print(f"[{device_id}] Disconnected.")
        del connected_devices[device_id]


@app.get("/devices")
async def get_connected_devices():
    """Retrieve the latest energy data from all devices."""
    return connected_devices
