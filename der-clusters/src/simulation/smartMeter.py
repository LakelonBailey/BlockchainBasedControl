
import os
import json
import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from src.utils.server import CentralServerAPI
from web3 import Web3
import threading
from time import sleep
from threading import Lock
import asyncio
from smartContract import send_transaction
from smartContract import orderbook_contract
from smartContract import spin_event_threads
from smartContract import printUserOrders
from smartContract import print_orderbook_state
import random

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]

# Constant: number of transactions to buffer before a batch upload.
TRANSACTION_BUFFER_SIZE = 4

# How many KwH the battery can hold 
BATTERY_CAPACITY = 13.5     #kWh
# moving average window to track battery
MOVING_AVERAGE_ALPHA = .1 # alpha = random.uniform(0.05, 0.3)

energy_moving_average = 0


battery = 0 # units are kWh
battery_lock = Lock()
energy_bought_from_grid_kWh = 0
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

def determine_sell_amount(trend, base_amount=1.0):
    global battery
    battery_ratio = battery / BATTERY_CAPACITY
    trend_strength = max(trend / BATTERY_CAPACITY, 0)  # Only positive trend encourages selling
    noise = random.uniform(-0.2, 0.2)

    adjustment = 0.6 * battery_ratio + 0.3 * trend_strength + 0.1 * noise
    return max(0.1, round(base_amount * adjustment, 2))

def determine_buy_amount(trend, base_amount=1.0):
    global battery
    empty_ratio = 1 - (battery / BATTERY_CAPACITY)
    trend_strength = max(-trend / BATTERY_CAPACITY, 0)  # Only negative trend encourages buying
    noise = random.uniform(-0.2, 0.2)

    adjustment = 0.6 * empty_ratio + 0.3 * trend_strength + 0.1 * noise
    return max(0.1, round(base_amount * adjustment, 2))

def update_battery_sync(device_type, energy_kwh):
    global battery, energy_bought_from_grid_kWh, energy_moving_average

    with battery_lock: 
        signed_kwh = energy_kwh if device_type == 'production' else -energy_kwh
        energy_moving_average = MOVING_AVERAGE_ALPHA * signed_kwh + (1 - MOVING_AVERAGE_ALPHA) * energy_moving_average

        if device_type == 'production':
            battery = energy_kwh + battery if energy_kwh + battery <= BATTERY_CAPACITY else BATTERY_CAPACITY
            ## If energy is needed, take from battery before you take from grid (assume grid has unlimited)
        if device_type == 'consumption':
            if battery >= energy_kwh:
                battery = battery - energy_kwh
        else:
            energy_bought_from_grid_kWh = energy_bought_from_grid_kWh + (battery - energy_kwh)
            battery = 0

        try:
            best_bid, best_ask, last_price = orderbook_contract.functions.getPrice().call()
        except Exception as e:
            print(f"Failed to fetch price: {e}")
            return
        #do automated trading logic 
        decision_threshold = random.uniform(0.05, 0.3)             #adds noise to automated trading decisions
        base_amount_multiplier = random.uniform(.05, .2)
        base_amount = round(BATTERY_CAPACITY * base_amount_multiplier, 2)
        order_type_prob = random.random()
        #volatility_factor = min(abs(energy_moving_average) / BATTERY_CAPACITY, 1.0)
        isMarket = True if order_type_prob < .20 else False        # maybe make this more dynamic

        if battery + energy_moving_average >= BATTERY_CAPACITY * (1-decision_threshold): # we are close to full battery and should sell some energy 
            sell_am = determine_sell_amount(energy_moving_average, base_amount)
            sell_am = (.5 * battery) if battery - sell_am < 0 else sell_am
            direction = random.choice([-1, 1])  # Randomly go above or below reference
            price_multiplier = random.triangular(0.0, 0.05, 0.02)
            limit_price = round((best_bid*(1+price_multiplier*direction)),2)
            try:
                #scale val
                send_transaction(
                    orderbook_contract.funcitons.placeOrder( # TODO descale by 100 for transaction notifications
                        int(sell_am * 100),             # quantity (scale by 100 because solidity does not have a decimal type)
                        int(limit_price * 100),         # price per unit
                        False,                          #isBuy
                        isMarket
                    )
                )
            except Exception as e:
                print(f"Failed to place sell order: {e}")

        if battery + energy_moving_average <= BATTERY_CAPACITY * decision_threshold: # we are close to empty and should buy energy
            buy_am = determine_buy_amount(energy_moving_average, base_amount)
            buy_am = (.5 * (BATTERY_CAPACITY - battery)) if battery + buy_am > BATTERY_CAPACITY else buy_am
            direction = random.choice([-1, 1])  # Randomly go above or below reference
            price_multiplier = random.triangular(0.0, 0.05, 0.02)
            limit_price = round((best_ask*(1+price_multiplier)),2)
            try:
                #scale val
                send_transaction(
                    orderbook_contract.funcitons.placeOrder( # TODO descale by 100 for transaction notifications
                        int(buy_am * 100),             # quantity (scale by 100 because solidity does not have a decimal type)
                        int(limit_price * 100),         # price per unit
                        True,                          #isBuy
                        isMarket
                    )
                )
            except Exception as e:
                print(f"Failed to place sell order: {e}")


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

                ## Add battery logic 
                ## If energy produced add it to the battery
                await asyncio.get_event_loop().run_in_executor(
                    None, update_battery_sync, device_type, energy_kwh
                )
               

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

@app.on_event("startup")
def on_startup():
    print("Spinning up Ethereum event threads...")
    spin_event_threads()