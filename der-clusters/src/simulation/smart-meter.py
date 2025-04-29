import os
import json
import logging
import asyncio
import subprocess
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.utils.server import CentralServerAPI

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
CHAIN_ID = os.environ.get("CHAIN_ID", None)
G_PORT = os.environ["G_PORT"]
HTTP_PORT = os.environ["HTTP_PORT"]
WS_PORT = os.environ["WS_PORT"]
AUTH_RPC_PORT = os.environ["AUTH_RPC_PORT"]
AUTH_ENODES = os.environ["AUTH_ENODES"]
DISABLE_BLOCKCHAIN = os.environ.get("DISABLE_BLOCKCHAIN", "false").lower() == "true"
# Interval in seconds by which the meter will ping the central server
PING_INTERVAL = 10

# FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

connected_devices = set()

# Create a separate CentralServerAPI instance for pinging in the background
global_server_api = CentralServerAPI(CLIENT_ID, CLIENT_SECRET, scope="smart_meter")


async def upload_enode(enode: str) -> requests.Response:
    """
    Sets the 'enode' field on the smart meter related to the given client id
    and client secret.

    Example usage:
    ```
    await upload_enode("enode://blahblablah@host:port")
    ```
    """
    return await global_server_api.post("/api/enodes/", {"enode": enode})


async def get_enodes() -> list[str]:
    """
    Returns the comprehensive enode list according to what is currently
    in the database.

    Example usage:
    ```
    enode_list = await get_enodes()
    ```
    """
    response = await global_server_api.get("/api/enodes/")
    return response.json()["enodes"]


async def make_enode_json():
    """
    This is how the config.toml file should look
    [Node.P2P]
    StaticNodes = [
      "enode://2b775bc162310dea781618d1ffc25477289460891565043ab899bc83d2ec1b166deea94d713a94611bf1abbbeec1fdf57b07aa2c6c604edda4039deeaf490951@138.197.32.246:30303?discport=30306",
      "enode://2df673c2cfa6a9696dda8cf2878373500ccfac39910f3869d2e61efdf5d51bab8b7a4310caee522db65d578ae0cfc64b87d3cd7470844ee2ae58fa645ac1c817@134.209.41.49:30301?discport=30310"
    ]
    """
    own_enode_file = "/app/auto-geth-setup/geth_node/enode.txt"
    with open(own_enode_file, "r") as file:
        own_enode = file.read()
    logger.info(f"------------>{own_enode}")
    own = await upload_enode(own_enode)

    await asyncio.sleep(10)

    enodes = await get_enodes()
    logger.info(enodes)
    enode_file = os.path.join("/app/auto-geth-setup/geth_node", "enodes.json")
    with open(enode_file, "w") as file:
        json.dump(enodes, file)
    with open(enode_file, "r") as file:
        enodes = json.load(file)
    auth_enodes = AUTH_ENODES.split(",")
    for auth in auth_enodes:
        enodes.append(auth)
    config = {"Node.P2P": {"StaticNodes": enodes}}
    # the config file will go in the data folder of the geth node, this dir is for the current docker setup
    config_file = os.path.join("/app/auto-geth-setup/geth_node/data", "config.toml")
    with open(config_file, "w") as file:
        file.write("[Node.P2P]\n")
        file.write("StaticNodes = [\n")
        # file.write('  "enode://42f53e6061ecd2df46ea0b15ec70afb48508464ecb99ec213627526be42fc86559b0395b7405e493660fd71614c6e9773c267757b54bb44970ff470891d9321b@138.197.32.246:30303?discport=0",\n')
        # file.write('  "enode://61df5fe2a47d32f4e3a2009c519b8f842b56b3c953c0cb014346afb3ad69ab77c23b1985e404c4324c19a4aaf95816610d451bbf3ef95fd787cbd7afd45cdb7d@209.97.156.6:30303?discport=0",\n')
        for enode in enodes:
            file.write(f'  "{enode}",\n')
        file.write("]\n")


async def geth_setup_async(port1, is_auth="n"):
    account = await asyncio.create_subprocess_exec(
        "python3",
        "-u",
        "/app/auto-geth-setup/geth_account_setup.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for line in account.stdout:
        print(line.decode(), end="")
    await account.wait()
    port = G_PORT

    init = await asyncio.create_subprocess_exec(
        "python3",
        "/app/auto-geth-setup/init_geth.py",
        f"{G_PORT}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for line in init.stdout:
        print(line.decode(), end="")
    await init.wait()

    await make_enode_json()

    config = await asyncio.create_subprocess_exec(
        "python3",
        "-u",
        "/app/auto-geth-setup/make_config_file.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for line in config.stdout:
        print(line.decode(), end="")
    await config.wait()

    proc = subprocess.Popen(
        [
            "python3",
            "-u",
            "/app/auto-geth-setup/run_node.py",
            f"{G_PORT}",
            f"{HTTP_PORT}",
            f"{WS_PORT}",
            f"{AUTH_RPC_PORT}",
            f"{CHAIN_ID}",
            f"{is_auth}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    for line in proc.stdout:
        logger.info(f"[GETH]: {line.strip()}")

    exit_code = proc.wait()
    logger.error(f"[GETH exited with code {exit_code}]")

    while True:
        await asyncio.sleep(10)


@app.on_event("startup")
async def start_ping_task():
    """
    On application startup, kick off an async task that pings the central server
    every 10 seconds.
    """
    # asyncio.create_task(geth_setup_async(8900))
    asyncio.create_task(ping_loop())


async def ping_loop():
    """
    Periodically pings the central server in an infinite loop.
    """
    if not DISABLE_BLOCKCHAIN:
        asyncio.create_task(geth_setup_async(8900))
    while True:
        try:
            await global_server_api.ping()
            logger.info("CentralServerAPI ping successful.")

        except Exception as e:
            logger.error(f"CentralServerAPI ping failed: {e}")

        # Sleep for 10 seconds before pinging again
        await asyncio.sleep(10)


@app.websocket("/ws/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    """
    WebSocket endpoint for receiving energy data from devices.
    """
    await websocket.accept()
    connected_devices.add(device_id)
    logger.info(f"Device Connected | ID: {device_id}")

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            device_id = message["device"]["id"]
            energy_kwh = message["energy_kwh"]
            timestamp = message["timestamp"]
            device_type = message["device"]["type"]

            # Log each energy transaction
            logger.info(
                f"Energy Transaction | ID: {device_id} | Type: {device_type} "
                f"| kWh: {energy_kwh:.8f}"
            )

    except WebSocketDisconnect:
        connected_devices.remove(device_id)
        logger.info(f"Device Disconnected | ID: {device_id}")


@app.get("/devices")
async def get_connected_devices():
    """Retrieve the latest connected devices."""
    return list(connected_devices)
