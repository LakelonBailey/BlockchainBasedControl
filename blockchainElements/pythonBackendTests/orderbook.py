from web3 import Web3
import json
import threading
from time import sleep
from collections import deque
from threading import Lock


w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

ACCOUNT = "0x2Ebd5B3998EEE2dd04C3d5a7BE595b9E8e336902"
KEYSTORE_FILE = "/home/tyanderson/litenode1/keystore/UTC--2025-03-26T16-19-19.906422369Z--2ebd5b3998eee2dd04c3d5a7be595b9e8e336902"
KEYSTORE_PASSWORD = "litenode1pw"
WEB3_PROVIDER = "http://localhost:8545"
TOKEN_ADDRESS = "0x2ef22142186cdbe0d1832cd9ffcbcf02be59dab0"




#   transactionHash: "0xad2348a5ff165f0b2ddb1226e86ff21efec08c795685251e998f7aad4ecc40ff"
CONTRACT_ADDRESS = "0x9FF73caE2F7dA1200ff948a16A1158189f347CA4"
CONTRACT_ADDRESS = w3.to_checksum_address(CONTRACT_ADDRESS)
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


seen_tx_hashes = deque(maxlen=100)
tx_lock = Lock()

def handle_event(event):
    #if event['event'] == 'OrderMatched'"

    print(f"\nNew Event: {event['event']}")
    print(f"Tx: {event['transactionHash'].hex()}, Block: {event['blockNumber']}")
    for key, value in event['args'].items():
        if isinstance(value, bytes):
            value = value.hex()
        print(f"  {key}: {value}")


def listen_for_events(event_name, filters):
    event = getattr(orderbook_contract.events, event_name)
    last_block = w3.eth.block_number
    print(f"Listening for {event_name} from block {last_block} with filters {filters}...")

    while True:
        current_block = w3.eth.block_number
        #logs = event.get_logs(fromBlock=last_block + 1, toBlock='latest', argument_filters=filters)
        logs = event.get_logs(from_block=last_block + 1, to_block='latest', argument_filters=filters)
        
        for log in logs:
            tx_hash = log['transactionHash'].hex()
            with tx_lock:
                if tx_hash not in seen_tx_hashes:
                    seen_tx_hashes.append(tx_hash)
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



if __name__ == "__main__":
    spin_event_threads()
    print("Event listeners started. Waiting a moment for threads to initialize...")
    sleep(3)  # Give threads a moment to start

    print("\nPlacing a limit buy order: 10 kWh @ 5 tokens/kWh")
    send_transaction(
        orderbook_contract.functions.placeOrder(
            5,  # energyAmount (kWh)
            5,   # pricePerUnit (tokens/kWh)
            False,  # isBuy
            True  # isMarket
        )
    )

    sleep(10)
    print_orderbook_state()

    '''    
    # 2. Place a limit buy order
    print("\nPlacing a limit buy order: 10 kWh @ 5 tokens/kWh")
    send_transaction(
        orderbook_contract.functions.placeOrder(
            10,  # energyAmount (kWh)
            5,   # pricePerUnit (tokens/kWh)
            True,  # isBuy
            False  # isMarket
        )
    )
    
    # 3. Place a limit sell order
    print("\nPlacing a limit sell order: 15 kWh @ 6 tokens/kWh")
    send_transaction(
        orderbook_contract.functions.placeOrder(
            5,  # energyAmount
            1,   # pricePerUnit
            False,  # isBuy
            False   # isMarket
        )
    )
    '''
    #send_transaction(orderbook_contract.functions.placeOrder(10, 4, True, False))
    #send_transaction(orderbook_contract.functions.placeOrder(8, 3, True, False))
    #send_transaction(orderbook_contract.functions.placeOrder(5, 2, True, False))
    #print("\nOrderbook state after limit orders:")
  




