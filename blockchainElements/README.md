## Setting Up a Node


### Install GETH that supports clique for Linux

sudo apt update && sudo apt upgrade -y
sudo apt install wget tar curl git build-essential -y

wget https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.13.14-2bd6bd01.tar.gz
tar -xvzf geth-linux-arm64-1.13.14-2bd6bd01.tar.gz
sudo mv geth-linux-arm64-1.13.14-2bd6bd01/geth /usr/local/bin/geth

### Create a genesis file on your validator node 

Check this directory for the genesis file

### Create a new data directory and account on your validator node 
```
geth --datadir ~/node1 account new
```
save the account address that it generates

In the genesis file, wherever you see an account address, replace it with your validator account address from above 

### Initialize the validator node with the genesis.json file
```
geth --datadir ~/node1 init ~/node1/genesis.json
```

### Run your node 
For a validator node run:
```
geth --datadir ~/node1 --networkid 1340 --port 30303 --unlock 0x3020c799B3eCdDdc3818D1ddeF1Ca48FC1A76244 --mine --miner.etherbase 0x3020c799B3eCdDdc3818D1ddeF1Ca48FC1A76244 --miner.gasprice 1 console
```
For a client/lite node run: 
```
geth --datadir ~/litenode1      --networkid 1340     --syncmode "snap" --port 30303 --unlock 0x2Ebd5B3998EEE2dd04C3d5a7BE595b9E8e336902  --config config.toml
```

Make sure you paste in your own node's aress in the 2 spots using it. Once it begins running, make sure you enter your password so the node can begin mining. 

### Running a lite node on the pi

Download geth like previously explained and repeat the steps of creating an account and compiling the genesis.json file. Do not change anything about the genesis.json file not even the account addresses.

When booting up the lite node, it needs to discover the authority nodes. Create a config.toml file that you will pass when booting up the lite node. This file can be found in this directory. Include the enode adresses of the validators that you want the lite node to discover. 

### Run the Litenode
```
geth --datadir ~/liteNode1      --networkid 1338      --syncmode "snap"      --http --http.addr 127.0.0.1 --http.port 8545     --port 30303 --config config.toml
```
I use "--syncmode snap" because litenode syncmode has been deptricated, but snap is the next lightest option


### Open a geth console and test
to open a geth console on any one of your running nodes, go into the node directory and find the geth.ipc file. Run:

geth attach geth.ipc

you can run commands like "eth.blockNumber" or "admin.peers" to make sure your nodes are visible to one another. 



## Deploying Smart Contracts 

### Compile Contracts with Remix
Use remix to compile the contracts. In remix you will see where you can copy the byte code and ABI for the smart contract. 

### JS Deployment scripts
The ABI and byte code is added to a JS script where that script can then be executed on the GETH command line and deployed. Add the script into your node's data directory and run:
```
loadScript('scriptName.js') 
```
In the Geth console 