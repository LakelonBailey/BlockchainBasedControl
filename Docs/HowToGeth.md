# Geth Install
## You will need GoLang
``` 
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
export GOPATH=$HOME/go
export PATH=$PATH:$GOPATH/bin
source ~/.bashrc
go version

```
## Install geth version 1.10.26, this comes with puppeth 
```
sudo apt update && sudo apt install -y build-essential golang
tar -xvf go-ethereum-1.10.26.tar.gz
cd go-ethereum
git checkout v1.10.26
make geth puppeth
```
## if make doesn't work
```
go run build/ci.go install ./cmd/geth ./cmd/puppeth
```

## move binaries to system path
```
sudo mv build/bin/geth build/bin/puppeth /usr/local/bin/
sudo chmod +x /usr/local/bin/geth /usr/local/bin/puppeth
```
## verify installation
```
geth version
puppeth
```
## Remove geth 1.10.26 and upgrade to geth 1.13.14

```
sudo rm /usr/local/bin/geth
geth version
wget https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.13.14-2bd6bd01.tar.gz
tar -xvf geth-linux-amd64-1.13.14-2bd6bd01.tar.gz
sudo mv geth-linux-arm64-1.13.14-2bd6bd01/geth /usr/local/bin/geth
geth version
```

# Begin making the private network
1. Make 3 directories node1, node2, signer_node `mkdir node1, node2, signer_node`
2. In each directory make a geth account `geth --datadir "./data" account new`. In a text file save the nodes public key and their passwords, you **can not recover** the public key address so this is important
3. In the root of the project, Use puppeth to make a genesis file, use the command `puppeth` to begin, 
* enter a name for the genesis file
* "2" to configure new genesis 
* then "1" to create from scratch
* "2" for clique POA chain
* Any time is fine, hit enter with no input for default value
* Paste the signer_nodes public key address for sealer
* pre fund any accounts you want with their public key address
* "yes" for wei
* Any chain number/ network id is fine but  you do need this value, you can find it anytime in the genesis file
* "2" manage existing genesis
* "2" to Export genesis configurations 
* if in the root of the project hit enter otherwise enter the path to it
* ctrl + d to exit puppeth
4. In each node directory enter `geth --datadir ./data init ../<GENESISFILE>.json`
5. Make a bootnode directory and in the directory generate a bootnode key `bootnode -genkey boot.key`
6. In a new terminal in the bootnode directory start the bootnode `bootnode -nodekey boot.key -verbosity 7 -addr "127.0.0.1:30301"`
7. The bootnode will return an enode, `enode://abc...30301`, save this value where you saved the public keys
8. in each node directory make a password.txt file that holds the nodes password and nothing else
9. Start the signer_node by in the directory enter `geth --datadir "./data"  --port <PORT> --bootnodes <ENODE> --authrpc.port <PORT2> --ipcdisable --allow-insecure-unlock  --http --http.corsdomain="https://remix.ethereum.org, http://127.0.0.1:8000" --http.api web3,eth,debug,personal,net --networkid <NETWORKID> --unlock <SIGNER_ADDRESS> --password password.txt  --mine --miner.etherbase=<SIGNER_ADDRESS>` Enter your own signer address, enode, chain number/network id. The ports should be different and different for each node
10. To start the light nodes in their directories enter `geth --datadir "./data"  --port <PORT> --bootnodes <ENODE>  -authrpc.port <PORT> --networkid <NETWORKID> --unlock <NODE_ADDRESS> --password password.txt --http.api web3,eth,debug,personal,net`
# Monitor the private network
1. In a new terminal go to the signer_node directory
2. Copy each of the light nodes key file, found in their keystore folder and file starts with UTC, into the signer nodes keystore folder
3. Attach the terminal to the geth console using `geth attach http://127.0.0.1:<SIGNER PORT>`
4. This allows you to monitor the network using the geth commands found here https://ethereum.stackexchange.com/questions/28703/full-list-of-geth-terminal-commands 
# Set up a Smart Contract
1. go to remix ethereum IDE at https://remix.ethereum.org/
2. Make new smart contract. here is a simple exchange script `TransferFunds.sol`
```
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TransferFunds {

    // This function sends funds from the contract to the specified address
    function sendFunds(address payable _to) public payable {
        require(msg.value > 0, "You must send some ether");
        
        // Transfer the ether to the recipient address
        _to.transfer(msg.value);
    }

    // Allow the contract to receive ETH
    receive() external payable {}
}
```
3. in the solidity compiler tab under the advanced configurations set the "EVM version" to "Paris" to work with a clique POA chain
4. Compile it and go to the deploy and run tab set the environment to the signer nodes ip and port with the custom - external http provider tab
5. attempt to deploy it
# Running the smart contract from a python script
1. after running it look for the contract address value, a hex value similar to the public keys, and then the abi value in the compilation tab, this looks like JSON data
2. here is a simple script to call the smart contract in python, you will need the web3 module
```
from web3 import Web3

# Connect to Geth node
web3 = Web3(Web3.HTTPProvider("http://localhost:8545"))  # Replace with your Geth RPC URL

# Check connection
if not web3.is_connected():
    raise Exception("Failed to connect to Ethereum node")

# Contract ABI (replace this with your actual contract ABI)
contract_abi = <ABI_VALUE>

# Contract address (Replace with your actual contract address)
contract_address = web3.to_checksum_address("0x829364C3E4BF172279ABC09B3C911CCA22615400")


# Create contract instance
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# Sender and recipient addresses
sender_address = web3.to_checksum_address("<sender_public_key_address>") #in the quotes
recipient_address = web3.to_checksum_address("<Reciever_public_key_address>")


# Private key of the sender (DO NOT expose this in production)
sender_private_key = "sender_private_key"  # Replace with your private key, you can get this with the script after this step

# Amount to send (in ETH)
amount_in_wei = web3.to_wei(1, "ether")  # Sending 1 ETH

# Get the nonce (transaction count) for the sender
nonce = web3.eth.get_transaction_count(sender_address)

# Build the transaction
txn = contract.functions.sendFunds(recipient_address).build_transaction({
    "from": sender_address,
    "value": amount_in_wei,  # Sending value in Wei
    "gas": 3000000,  # Set gas limit
    "gasPrice": web3.to_wei(10, "gwei"),  # Gas price in Gwei
    "nonce": nonce  # Ensure unique transaction
})

# Sign the transaction with the sender's private key
signed_txn = web3.eth.account.sign_transaction(txn, sender_private_key)

# Send the signed transaction
tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

# Print transaction hash
print(f"Transaction sent! Hash: {web3.to_hex(tx_hash)}")


```   
3. If you need the private key address you can use this python script, you will need the eth_keyfile module via pip
```
import json
from eth_keyfile import decode_keyfile_json

# Replace with your actual keystore file path
keystore_path = "PATH_TO_SENDERS_KEYSTORE_FILE"

# Load keystore JSON
with open(keystore_path, "r") as keyfile:
    encrypted_key = json.load(keyfile)

# Prompt for password (DO NOT hardcode passwords)
password = input("Enter password: ").encode()

# Decrypt the private key
private_key = decode_keyfile_json(encrypted_key, password)

print("Your Private Key:", private_key.hex())

```
