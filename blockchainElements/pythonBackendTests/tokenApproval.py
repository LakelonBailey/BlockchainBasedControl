from web3 import Web3
import json

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

with open("tokenABI.json") as f:
    token_abi = json.load(f)

with open(KEYSTORE_FILE) as f:
    keystore_json = json.load(f)

private_key = w3.eth.account.decrypt(keystore_json, KEYSTORE_PASSWORD)
account = w3.eth.account.from_key(private_key)

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


token_contract = w3.eth.contract(address=w3.to_checksum_address(TOKEN_ADDRESS), abi=token_abi)  # ERC20 ABI from OpenZeppelin
send_transaction(
    token_contract.functions.approve(CONTRACT_ADDRESS, w3.to_wei(1000, 'ether'))  # Approve 1000 tokens
)