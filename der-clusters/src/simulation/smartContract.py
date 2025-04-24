from web3 import Web3
import json
import threading
from time import sleep
from collections import deque
from threading import Lock
import os
from smartMeter import battery_lock
import smartMeter
from smartMeter import BATTERY_CAPACITY

#w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

#ACCOUNT = "0x2Ebd5B3998EEE2dd04C3d5a7BE595b9E8e336902"
#KEYSTORE_FILE = "/home/tyanderson/litenode1/keystore/UTC--2025-03-26T16-19-19.906422369Z--2ebd5b3998eee2dd04c3d5a7be595b9e8e336902"
#KEYSTORE_PASSWORD = "litenode1pw"
#WEB3_PROVIDER = "http://localhost:8545"

#CONTRACT_ADDRESS = "0x21B74a3b51Ba7233c1B60a544cb22D1554683299"
#CONTRACT_ADDRESS = w3.to_checksum_address(CONTRACT_ADDRESS)

ACCOUNT = os.environ["ACCOUNT"]
KEYSTORE_FILE = os.environ["KEYSTORE_FILE"]
KEYSTORE_PASSWORD = os.environ["KEYSTORE_PASSWORD"]

WEB3_PROVIDER = os.environ["WEB3_PROVIDER"]
TOKEN_ADDRESS = os.environ["TOKEN_ADDRESS"]
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

CONTRACT_ADDRESS = os.environ["CONTRACT_ADDRESS"]
CONTRACT_ADDRESS = w3.to_checksum_address(CONTRACT_ADDRESS)
ABI_JSON_PATH = os.environ["ABI_JSON_PATH"]

if w3.is_connected():
    print("Connected to node!")
    print(f"Chain ID: {w3.eth.chain_id}")
    print(f"Block Number: {w3.eth.block_number}")
else:
    print("Failed to connect to node. Check if geth is running with --http on port 8545.")



with open(KEYSTORE_FILE) as f:
    keystore_json = json.load(f)

private_key = w3.eth.account.decrypt(keystore_json, KEYSTORE_PASSWORD)
account = w3.eth.account.from_key(private_key)

with open("updatedOrderBookABI.json") as f:
    contract_abi = json.load(f)

orderbook_contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=contract_abi)

# sends a transaction triggering a blockchain event
def send_transaction(function, value=0):
    tx = function.build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'gas': 2000000,  # Adjust based on contract complexity
        'gasPrice': w3.to_wei('1', 'gwei'),
        'chainId': 1340,  # Your PoA network ID
        'value': value
    })
    signed_tx = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction sent: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Confirmed in block {receipt.blockNumber}")
    return receipt

# prints all of the buy orders and all of the sell orders from the on-chain orderbook
def print_orderbook_state():
    buy_orders = orderbook_contract.functions.getBuyOrders().call()
    sell_orders = orderbook_contract.functions.getSellOrders().call()
    best_bid, best_ask, last_price = orderbook_contract.functions.getPrice().call()
    print(f"Buy Orders: {len(buy_orders)}")
    for order in buy_orders:
        print(f"  {order}")
    print(f"Sell Orders: {len(sell_orders)}")
    for order in sell_orders:
        print(f"  {order}")
    print(f"Best Bid: {best_bid}, Best Ask: {best_ask}, Last Price: {last_price}")


# A local coppy of all the orders that a user makes
orders      : dict[str, dict] = {} 
orders_lock = Lock()

def printUserOrders():
    if not orders:
        print("No orders \n")
        return

    for oid, data in orders.items():
        # Build “key=value” parts for the inner dictionary
        inner = ", ".join(f"{k}={v}" for k, v in data.items())
        print(f"{oid}: {inner}")
    print()  

def updateOrder(buyerOId, sellerOId, quantity):
    with battery_lock:
        if buyerOId in orders:
            smartMeter.battery = min(smartMeter.battery + quantity, BATTERY_CAPACITY)
        elif sellerOId in orders:
            smartMeter.battery = max(smartMeter.battery - quantity, 0)

    with orders_lock:
        oid = buyerOId if buyerOId in orders else sellerOId
        if oid not in orders: return False 

        o = orders.get(oid)
        o['qty'] -= quantity
        if o['qty'] <= 0:
            orders.pop(oid, None)


def addOrder(orderId, isBuy, amount, pricePerUnit, isMarket):
    if not isMarket:
        with orders_lock:
            orders[orderId] = dict(
                side   = "buy" if isBuy else "sell",
                qty    = amount,
                price  = pricePerUnit
            )

def removeOrder(orderId):
    with orders_lock:
        o = orders.pop(orderId, None)


def handle_event(event):

    print(f"\nNew Event: {event['event']}")
    print(f"Tx: {event['transactionHash'].hex()}, Block: {event['blockNumber']}")
    for key, value in event['args'].items():
        if isinstance(value, bytes):
            value = value.hex()
        print(f"  {key}: {value}")


    if event['event'] == 'OrderMatched':
        oid = Web3.to_hex(event['args']['buyerOrderId'])
        updateOrder(oid, event['args']['sellerOrderId'], event['args']['energyAmount'])
    #add orderId to OrderCanceled
    if event['event'] == 'OrderCanceled':
        oid = Web3.to_hex(event['args']['oid'])
        removeOrder(oid)
    if event['event'] == 'OrderPlaced':
        oid = Web3.to_hex(event['args']['orderId'])
        addOrder(oid, event['args']['isBuy'], event['args']['amount'], event['args']['pricePerUnit'], event['args']['market'])




seen_tx_hash_OrderPlaced = deque(maxlen=20)
seen_tx_hash_OrderCancelled = deque(maxlen=20)
seen_tx_hash_OrderMatchedBuyer = deque(maxlen=20)
seen_tx_hash_OrderMatchedSeller = deque(maxlen=20)

def listen_for_events(event_name, filters):
    event = getattr(orderbook_contract.events, event_name)
    last_block = w3.eth.block_number
    print(f"Listening for {event_name} from block {last_block} with filters {filters}...")

    while True:
        current_block = w3.eth.block_number
        #logs = event.get_logs(fromBlock=last_block + 1, toBlock='latest', argument_filters=filters)
        logs = event.get_logs(from_block=last_block + 1, to_block='latest', argument_filters=filters)
        
        for log in logs:
            tx_hash = (log['transactionHash'].hex(), log['logIndex'])

            if event_name == 'OrderPlaced':
                if tx_hash not in seen_tx_hash_OrderPlaced:
                    seen_tx_hash_OrderPlaced.append(tx_hash)
                    handle_event(log)
            elif event_name == 'OrderCancelled':
                if tx_hash not in seen_tx_hash_OrderCancelled:
                    seen_tx_hash_OrderCancelled.append(tx_hash)
                    handle_event(log)
            elif event_name == 'OrderMatched' and 'buyer' in filters:
                if tx_hash not in seen_tx_hash_OrderMatchedBuyer:
                    seen_tx_hash_OrderMatchedBuyer.append(tx_hash)
                    handle_event(log)
            elif event_name == 'OrderMatched' and 'seller' in filters:
                if tx_hash not in seen_tx_hash_OrderMatchedSeller:
                    seen_tx_hash_OrderMatchedSeller.append(tx_hash)
                    handle_event(log)

        last_block = current_block
        sleep(2)

def spin_event_threads():
    event_configs = [
        ('OrderPlaced', {'user': ACCOUNT}),
        ('OrderCancelled', {'user': ACCOUNT}),
        ('OrderMatched', {'buyer': ACCOUNT}),
        ('OrderMatched', {'seller': ACCOUNT})
    ]
    
    for event_name, filters in event_configs:
        thread = threading.Thread(target=listen_for_events, args=(event_name, filters))
        thread.daemon = True
        thread.start()




