from web3 import Web3
import json
import threading
from time import sleep


w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))

ACCOUNT = "0x2Ebd5B3998EEE2dd04C3d5a7BE595b9E8e336902"
KEYSTORE_FILE = "/home/tyanderson/litenode1/keystore/UTC--2025-03-26T16-19-19.906422369Z--2ebd5b3998eee2dd04c3d5a7be595b9e8e336902"
KEYSTORE_PASSWORD = "litenode1pw"
WEB3_PROVIDER = "http://localhost:8545"
TOKEN_ADDRESS = "0x2ef22142186cdbe0d1832cd9ffcbcf02be59dab0"




#   transactionHash: "0xad2348a5ff165f0b2ddb1226e86ff21efec08c795685251e998f7aad4ecc40ff"
CONTRACT_ADDRESS = "0x1610b609fef0287c095ab282d6e769b9a7ade4d8"
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

with open("orderbookABI.json") as f:
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


def handle_event(event):
    print(f"\nNew Event: {event['event']}")
    print(f"Tx: {event['transactionHash'].hex()}, Block: {event['blockNumber']}")
    for key, value in event['args'].items():
        if isinstance(value, bytes):
            value = value.hex()
        print(f"  {key}: {value}")

def listen_for_events(event_name, filters):
    event = getattr(orderbook_contract.events, event_name)
    event_filter = event.create_filter(from_block='latest', argument_filters=filters)
    print(f"Listening for {event_name} events with filters {filters}...")
    while True:
        for event in event_filter.get_new_entries():
            handle_event(event)
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
            15,  # energyAmount
            6,   # pricePerUnit
            False,  # isBuy
            False   # isMarket
        )
    )

    print("\nOrderbook state after limit orders:")
    print_orderbook_state()


