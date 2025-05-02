import os
import json
import logging
import asyncio
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.utils.server import CentralServerAPI
from web3 import Web3
import threading
from time import sleep
from threading import Lock
import random
from collections import deque
import websockets
import time
import math

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
CHAIN_ID = os.environ.get("CHAIN_ID", None)
G_PORT = os.environ["G_PORT"]
HTTP_PORT = os.environ["HTTP_PORT"]
WS_PORT = os.environ["WS_PORT"]
AUTH_RPC_PORT = os.environ["AUTH_RPC_PORT"]
AUTH_ENODES = os.environ["AUTH_ENODES"]
CONTRACT_ABI_PATH = os.environ["CONTRACT_ABI_PATH"]
CONTRACT_ADDRESS = os.environ["CONTRACT_ADDRESS"]
DISABLE_BLOCKCHAIN = os.environ.get("DISABLE_BLOCKCHAIN", "false").lower() == "true"
WEB3_PROVIDER = f"http://localhost:{HTTP_PORT}"
ACCOUNT = None

# Interval in seconds by which the meter will ping the central server
PING_INTERVAL = 10

# limit to 1 trade per 10 seconds
TRADE_WAIT_TIME = 10
last_trade = 0

# How many KwH the battery can hold
BATTERY_CAPACITY = 400

# moving average window to track battery
MOVING_AVERAGE_ALPHA = random.uniform(0.05, 0.3)

# Margin between quantity and price to place another order
SEND_ORDER_MARGIN = 0.5

# Energy price when the order books are empty and nothing has been executed
BASE_KWH_PRICE = 0.13  # TN's rate
# the moving average of net energy production
energy_moving_average = 0

battery = int(BATTERY_CAPACITY * 0.5)  # kWh
battery_lock = Lock()
energy_bought_from_grid_kWh = 0
main_loop: asyncio.AbstractEventLoop = None
# for synchronizing stats across connections
energy_stats_lock = asyncio.Lock()

# sliding window of the last 10 kWh values
recent_kwh: list[float] = []

# total number of energy‐transactions seen so far
transaction_count = 0


private_key = None
account = None
orderbook_contract = None
w3 = None
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
global_server_api = CentralServerAPI(CLIENT_ID, CLIENT_SECRET, scope="smart_meter")
blockchain_started = False
blockchain_started_lock = Lock()


# store user orders
orders: dict[str, dict] = {}
orders_lock = Lock()




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
    await upload_enode(own_enode)

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

    # the config file will go in the data folder of the geth node, this dir is for the current docker setup
    config_file = os.path.join("/app/auto-geth-setup/geth_node/data", "config.toml")
    with open(config_file, "w") as file:
        file.write("[Node.P2P]\n")
        file.write("StaticNodes = [\n")
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

    proc = await asyncio.create_subprocess_exec(
        "python3",
        "-u",
        "/app/auto-geth-setup/run_node.py",
        f"{G_PORT}",
        f"{HTTP_PORT}",
        f"{WS_PORT}",
        f"{AUTH_RPC_PORT}",
        f"{CHAIN_ID}",
        f"{is_auth}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    time.sleep(5)
    print("Spinning up Ethereum event threads...")
    await spin_event_threads()

    uri = "ws://144.126.248.158:8000/ws"
    password = "blockchain123"
    async with websockets.connect(uri) as ws:
        auth_payload = {"password": password}  # ← replace with your actual password
        await ws.send(json.dumps(auth_payload))
        auth_resp = await ws.recv()
        logger.info(auth_resp)

        account_payload = {"account": ACCOUNT}  # ← populate with your account data
        await ws.send(json.dumps(account_payload))
        reply = await ws.recv()
        print("Server reply:", reply)

    global blockchain_started
    with blockchain_started_lock:
        blockchain_started = True

    async for line in proc.stdout:
        logger.info(f"[GETH]: {line.strip()}")
    await proc.wait()

    logger.error(f"[GETH exited with code {proc.returncode}]")


@app.on_event("startup")
async def start_ping_task():
    """
    On application startup, kick off an async task that pings the central server
    every 10 seconds.
    """
    global main_loop
    main_loop = asyncio.get_running_loop()
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


def send_transaction(function, value=0):
    tx = function.build_transaction(
        {
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 2000000,  # Adjust based on contract complexity
            "gasPrice": w3.to_wei("1", "gwei"),
            "chainId": int(CHAIN_ID),  # Your PoA network ID
            "value": value,
        }
    )
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Confirmed in block {receipt.blockNumber}")
    return receipt


def printUserOrders():
    if not orders:
        print("No orders \n")
        return
    for oid, data in orders.items():
        # Build “key=value” parts for the inner dictionary
        inner = ", ".join(f"{k}={v}" for k, v in data.items())
        print(f"{oid}: {inner}")
    print()


def updateOrder(buyerOId, sellerOId, quantity, exec_price):
    global battery
    with battery_lock:
        if buyerOId in orders:
            battery = min(battery + quantity, BATTERY_CAPACITY)
        elif sellerOId in orders:
            battery = max(battery - quantity, 0)

    with orders_lock:
        oid = buyerOId if buyerOId in orders else sellerOId
        if oid not in orders:
            return False
        o = orders.get(oid)
        o["executed_price"] = exec_price

        is_first_transaction = o["curr_qty"] == o["origin_qty"]
        o["curr_qty"] -= quantity
        if o["curr_qty"] <= 0:
            orders.pop(oid, None)

        if is_first_transaction:
            asyncio.run_coroutine_threadsafe(
                global_server_api.update_order(oid, {"state": "matched"}), main_loop
            )

        asyncio.run_coroutine_threadsafe(
            global_server_api.create_transaction(
                oid, {"amount": quantity, "executed_price": exec_price}
            ),
            main_loop,
        )


def addOrder(orderId, isBuy, amount, pricePerUnit, isMarket):
    if not isMarket:
        with orders_lock:
            order_type = "buy" if isBuy else "sell"
            orders[orderId] = dict(
                side=order_type,
                origin_qty=amount,  # the original quantity that the user wants to buy/sell - does not change
                user_price=pricePerUnit,  # the price that the user submits the buy/sell order at
                executed_price=-1,  # the price that the most recently updated transaction executes at -> this value gets updated
                curr_qty=amount,  # how much quantity is still outstanding -> this value gets updated
            )
            asyncio.run_coroutine_threadsafe(
                global_server_api.create_order(
                    orderId,
                    {
                        "order_type": order_type,
                        "total_amount": amount,
                        "price": pricePerUnit,
                    },
                ),
                main_loop,
            )


def removeOrder(orderId):
    with orders_lock:
        orders.pop(orderId, None)


def handle_event(event):

    logger.info(f"\nNew Event: {event['event']}")
    logger.info(f"Tx: {event['transactionHash'].hex()}, Block: {event['blockNumber']}")

    for key, value in event["args"].items():
        if isinstance(value, bytes):
            value = value.hex()
        # print(f"  {key}: {value}")
        logger.info(f"  {key}: {value}")

    if event["event"] == "OrderMatched":
        buyer_oid = Web3.to_hex(event["args"]["buyerOrderId"])
        seller_oid = Web3.to_hex(event["args"]["sellerOrderId"])
        energy_am = event["args"]["energyAmount"] / 100
        exec_price = event["args"]["pricePerUnit"] / 100
        updateOrder(buyer_oid, seller_oid, energy_am, exec_price)

    # add orderId to OrderCanceled
    if event["event"] == "OrderCanceled":
        oid = Web3.to_hex(event["args"]["oid"])
        removeOrder(oid)

    if event["event"] == "OrderPlaced":
        oid = Web3.to_hex(event["args"]["orderId"])
        price = event["args"]["pricePerUnit"] / 100
        energy_am = event["args"]["amount"] / 100
        addOrder(oid, event["args"]["isBuy"], energy_am, price, event["args"]["market"])


# collect broadcasted messages sent from smart contract
seen_tx_hash_OrderPlaced = deque(maxlen=20)
seen_tx_hash_OrderCancelled = deque(maxlen=20)
seen_tx_hash_OrderMatchedBuyer = deque(maxlen=20)
seen_tx_hash_OrderMatchedSeller = deque(maxlen=20)


def listen_for_events(event_name, filters):
    event = getattr(orderbook_contract.events, event_name)
    last_block = w3.eth.block_number
    print(
        f"Listening for {event_name} from block {last_block} with filters {filters}..."
    )

    while True:
        current_block = w3.eth.block_number
        # logs = event.get_logs(fromBlock=last_block + 1, toBlock='latest', argument_filters=filters)
        logs = event.get_logs(
            from_block=last_block + 1, to_block="latest", argument_filters=filters
        )

        for log in logs:
            tx_hash = (log["transactionHash"].hex(), log["logIndex"])

            if event_name == "OrderPlaced":
                if tx_hash not in seen_tx_hash_OrderPlaced:
                    seen_tx_hash_OrderPlaced.append(tx_hash)
                    handle_event(log)
            elif event_name == "OrderCancelled":
                if tx_hash not in seen_tx_hash_OrderCancelled:
                    seen_tx_hash_OrderCancelled.append(tx_hash)
                    handle_event(log)
            elif event_name == "OrderMatched" and "buyer" in filters:
                if tx_hash not in seen_tx_hash_OrderMatchedBuyer:
                    seen_tx_hash_OrderMatchedBuyer.append(tx_hash)
                    handle_event(log)
            elif event_name == "OrderMatched" and "seller" in filters:
                if tx_hash not in seen_tx_hash_OrderMatchedSeller:
                    seen_tx_hash_OrderMatchedSeller.append(tx_hash)
                    handle_event(log)

        last_block = current_block
        sleep(2)


async def spin_event_threads():
    # TODO: Initialize all Web3 client info, find account, etc.
    # TODO: Initialize all Web3 client info, find account, etc.
    global ACCOUNT

    while not os.path.exists("/app/auto-geth-setup/geth_node/address.txt"):
        await asyncio.sleep(1)

    global private_key, account, orderbook_contract, w3
    with open("/app/auto-geth-setup/geth_node/address.txt", "r") as account_file:
        ACCOUNT = (
            account_file.read()
        )  # account address generated when creating geth account
    with open("/app/auto-geth-setup/geth_node/key.txt", "r") as key_file:
        KEYSTORE_PATH = (
            key_file.read()
        )  # Path to keystore file generated when creating geth account
    KEYSTORE_FILE = "/app/auto-geth-setup/geth_node/" + str(KEYSTORE_PATH)
    with open("/app/auto-geth-setup/geth_node/password.txt", "r") as password:
        KEYSTORE_PASSWORD = password.read()  # /password.txt after geth setup
    logger.info(f"keystore pw{KEYSTORE_PASSWORD}   http addr {WEB3_PROVIDER}")

    w3 = Web3(
        Web3.HTTPProvider(WEB3_PROVIDER)
    )  # Initialized as None at first. Will be changed AFTER geth account setup
    CONTRACT_ADDRESS = w3.to_checksum_address(
        os.environ["CONTRACT_ADDRESS"]
    )  # Initialized on-demand after geth account setup
    if w3.is_connected():
        print("Connected to node!")
        print(f"Chain ID: {w3.eth.chain_id}")
        print(f"Block Number: {w3.eth.block_number}")
    else:
        print(
            "Failed to connect to node. Check if geth is running with --http on port 8545."
        )

    with open(KEYSTORE_FILE) as f:
        keystore_json = json.load(f)
    with open("/app/auto-geth-setup/orderbookABI.json") as f:
        contract_abi = json.load(f)

    private_key = w3.eth.account.decrypt(keystore_json, KEYSTORE_PASSWORD)
    account = w3.eth.account.from_key(private_key)
    orderbook_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

    event_configs = [
        ("OrderPlaced", {"user": ACCOUNT}),
        ("OrderCancelled", {"user": ACCOUNT}),
        ("OrderMatched", {"buyer": ACCOUNT}),
        ("OrderMatched", {"seller": ACCOUNT}),
    ]

    for event_name, filters in event_configs:
        thread = threading.Thread(target=listen_for_events, args=(event_name, filters))
        thread.daemon = True
        thread.start()


def determine_sell_amount(trend, base_amount=1.0):
    global battery
    battery_ratio = battery / BATTERY_CAPACITY
    trend_strength = max(
        trend / BATTERY_CAPACITY, 0
    )  # Only positive trend encourages selling
    noise = random.uniform(-0.2, 0.2)

    adjustment = 0.6 * battery_ratio + 0.3 * trend_strength + 0.1 * noise
    return max(0.1, round(base_amount * adjustment, 2))


def determine_buy_amount(trend, base_amount=1.0):
    global battery
    empty_ratio = 1 - (battery / BATTERY_CAPACITY)
    trend_strength = max(
        -trend / BATTERY_CAPACITY, 0
    )  # Only negative trend encourages buying
    noise = random.uniform(-0.2, 0.2)

    adjustment = 0.6 * empty_ratio + 0.3 * trend_strength + 0.1 * noise
    return max(0.1, round(base_amount * adjustment, 2))


def validate_trade(order_type, amount, price):
    return True
    for order_id, order_info in orders.items():
        if order_type == order_info["side"]:
            if (abs(order_info["curr_qty"] - amount) / amount) <= 0.05 and (
                abs(order_info["user_price"] - price) / price
            ) <= 0.10:
                return False

    return True


def normal_round(n):
    if n - math.floor(n) < 0.5:
        return math.floor(n)
    return math.ceil(n)


# automates trading. More likely to make a trade when battery is full/empty
def determine_trades():
    try:
        best_bid, best_ask, last_price = orderbook_contract.functions.getPrice().call()
        best_bid = best_bid / 100
        best_ask = best_ask / 100
        last_price = last_price / 100
    except Exception as e:
        print(f"Failed to fetch price: {e}")
        return

    decision_threshold = random.uniform(
        0.05, 0.3
    )  # adds noise to automated trading decisions
    base_amount_multiplier = random.uniform(0.05, 0.2)
    base_amount = round(BATTERY_CAPACITY * base_amount_multiplier, 2)
    order_type_prob = random.random()
    # volatility_factor = min(abs(energy_moving_average) / BATTERY_CAPACITY, 1.0)
    isMarket = True if order_type_prob < 0.20 else False  # maybe make this more dynamic
    # ******* SELL ********
    if battery + energy_moving_average >= BATTERY_CAPACITY * (
        1 - decision_threshold
    ):  # we are close to full battery and should sell some energy
        logger.info(
            f"We are inside of the sell block. Battery: {battery}       Energy Moving Average {energy_moving_average}"
        )
        sell_am = determine_sell_amount(energy_moving_average, base_amount)
        sell_am = (0.5 * battery) if battery - sell_am < 0 else sell_am
        # direction = random.choice([-1, 1])  # Randomly go above or below reference
        # if your battery is neering full you are more likely to sell for less
        price_multiplier = (
            random.triangular(0.0, -0.10, 0.0)
            if battery / BATTERY_CAPACITY < 0.85
            else random.triangular(0.0, -0.20, -0.10)
        )
        my_bid = best_bid if best_bid > 0 else BASE_KWH_PRICE
        limit_price = my_bid * (1 + price_multiplier)
        limit_price *= 100
        limit_price = "{:.2f}".format(limit_price)
        limit_price = normal_round(float(limit_price))

        logger.info(f"********** LIMIT PRICE FOR SELL: {limit_price} ***********")
        if validate_trade("sell", sell_am, limit_price):
            logger.info(
                f"***** Aproved To Sell.  Moving average: {energy_moving_average}   Battery level: {battery}**********"
            )
            try:
                # scale val
                send_transaction(
                    orderbook_contract.functions.placeOrder(  # TODO descale by 100 for transaction notifications
                        int(
                            sell_am * 100
                        ),  # quantity (scale by 100 because solidity does not have a decimal type)
                        int(limit_price),  # price per unit
                        False,  # isBuy
                        isMarket,
                    )
                )
            except Exception as e:
                print(f"Failed to place sell order: {e}")
    # ***** BUY *******
    if (
        battery + energy_moving_average <= BATTERY_CAPACITY * decision_threshold
    ):  # we are close to empty and should buy energy
        logger.info(
            f"We are inside of the buy block. Battery: {battery}       Energy Moving Average {energy_moving_average}"
        )
        buy_am = determine_buy_amount(energy_moving_average, base_amount)
        buy_am = (
            (0.5 * (BATTERY_CAPACITY - battery))
            if battery + buy_am > BATTERY_CAPACITY
            else buy_am
        )
        # direction = random.choice([-1, 1])  # Randomly go above or below reference
        # if your battery is neering empty you are more willing to pay a higher price
        price_multiplier = (
            random.triangular(0.0, 0.10, 0.00)
            if battery / BATTERY_CAPACITY > 0.15
            else random.triangular(0.0, 0.20, 0.10)
        )
        my_ask = best_ask if best_ask > 0 else BASE_KWH_PRICE
        limit_price = my_ask * (1 + price_multiplier)
        limit_price *= 100
        limit_price = "{:.2f}".format(limit_price)
        limit_price = normal_round(float(limit_price))

        if validate_trade("buy", buy_am, limit_price):
            logger.info(
                f"***** Aproved To Buy.  Moving average: {energy_moving_average}   Battery level: {battery}**********"
            )

            try:
                # scale val
                send_transaction(
                    orderbook_contract.functions.placeOrder(
                        int(
                            buy_am * 100
                        ),  # quantity (scale by 100 because solidity does not have a decimal type)
                        int(limit_price),  # price per unit
                        True,  # isBuy
                        isMarket,
                    )
                )
            except Exception as e:
                print(f"Failed to place sell order: {e}")


# Called every time a client reports an energy update to the websocket
def update_battery_sync(device_type, energy_kwh):
    global battery, energy_bought_from_grid_kWh, energy_moving_average, last_trade

    with battery_lock:
        signed_kwh = energy_kwh if device_type == "production" else -energy_kwh
        energy_moving_average = (
            MOVING_AVERAGE_ALPHA * signed_kwh
            + (1 - MOVING_AVERAGE_ALPHA) * energy_moving_average
        )

        if device_type == "production":
            battery = (
                energy_kwh + battery
                if energy_kwh + battery <= BATTERY_CAPACITY
                else BATTERY_CAPACITY
            )
            # If energy is needed, take from battery before you take from grid (assume grid has unlimited)
        if device_type == "consumption":
            if battery >= energy_kwh:
                battery = battery - energy_kwh
            else:
                energy_bought_from_grid_kWh = energy_bought_from_grid_kWh + (
                    battery - energy_kwh
                )
                battery = 0

        current_time = time.time()
        if current_time - last_trade >= TRADE_WAIT_TIME:
            determine_trades()
            last_trade = time.time()
        logger.info(f"Battery: {battery}")
        logger.info(f"Battery Capacity: {BATTERY_CAPACITY}")


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
            device_type = message["device"]["type"]

            # track average over the last 10 transactions
            global transaction_count
            async with energy_stats_lock:
                transaction_count += 1
                recent_kwh.append(
                    energy_kwh * (-1 if device_type == "consumption" else 1)
                )
                if len(recent_kwh) > 10:
                    recent_kwh.pop(0)

                # every 10th transaction, log the net of the last 10
                if transaction_count % 10 == 0:
                    net_kwh = sum(recent_kwh)
                    logger.info(
                        f"Net energy over last 10 transactions: {net_kwh:.8f} kWh"
                    )

            with blockchain_started_lock:
                if not blockchain_started:
                    continue
            await asyncio.get_event_loop().run_in_executor(
                None, update_battery_sync, device_type, energy_kwh
            )

            # Log each energy transaction.
            # Log each energy transaction
    #        logger.info(
    #           f"Energy Transaction | ID: {device_id} | Type: {device_type} "
    #           f"| kWh: {energy_kwh:.8f}"
    #      )

    except WebSocketDisconnect:
        connected_devices.remove(device_id)
        logger.info(f"Device Disconnected | ID: {device_id}")


@app.get("/devices")
async def get_connected_devices():
    """Retrieve the latest connected devices."""
    return list(connected_devices)


@app.get("/user-orders")
async def get_user_orders():
    global orders
    return orders


@app.get("/orderbook")
async def get_blockchain_orderbook():
    try:
        buy_orders = orderbook_contract.functions.getBuyOrders().call()
        sell_orders = orderbook_contract.functions.getSellOrders().call()
        best_bid, best_ask, last_price = orderbook_contract.functions.getPrice().call()
    except Exception as e:
        return {"error": f"Failed to fetch data from contract: {str(e)}"}

    return {
        "buy_orders": buy_orders,
        "sell_orders": sell_orders,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "last_price": last_price,
    }
