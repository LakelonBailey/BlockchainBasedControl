# Requirements
* Python 3
* Geth bootnode (instructions below)
* Go-lang (instructions below)
* Geth 1.13.14 (instructions below)

## Go-Lang install

1. Remove any previous Go installation by deleting the /usr/local/go folder (if it exists), then extract the archive you just downloaded into /usr/local, creating a fresh Go tree in /usr/local/go (You may need to run the command as root or through sudo) :

    `$ rm -rf /usr/local/go && tar -C /usr/local -xzf go1.24.2.linux-amd64.tar.gz`      

2. Add /usr/local/go/bin to the PATH environment variable. You can do this by adding the following line to your $HOME/.profile or /etc/profile (for a system-wide installation): 

    `export PATH=$PATH:/usr/local/go/bin`
3. Verify that you've installed Go by opening a command prompt and typing the following command: 
    
    `go version`

## Bootnode install
1. To get the bootnode module we need to first get an earlier version of geth using: 
```
sudo apt update && sudo apt install -y build-essential golang
tar -xvf go-ethereum-1.10.26.tar.gz
cd go-ethereum
```
2. then build the bootnode with

* `go build -o build/bin/bootnode ./cmd/bootnode`

   or if that doesnt work

* `go run build/ci.go install ./cmd/bootnode`
3. move build to system path
```
sudo mv build/bin/bootnode /usr/local/bin/
sudo chmod +x /usr/local/bin/bootnode
```
4. Verify install `bootnode --help`

## Geth install
1. Get the geth tar:

     `wget https://gethstore.blob.core.windows.net/builds/geth-linux-arm64-1.13.14-2bd6bd01.tar.gz`
2. Extract the tar file 

    `tar -xvf geth-linux-amd64-1.13.14-2bd6bd01.tar.gz`
3. Move geth to binaries 
    
    `sudo mv geth-linux-arm64-1.13.14-2bd6bd01/geth /usr/local/bin/geth`
4. Verify install `Geth --version` or `Geth version`
### make sure you are in the geth-auto-setup directory
`cd geth-auto-setup`

## Set up the Geth accounts
1. run the `geth_account_setup.py` passing 2 arguements, node names (seperated by commas) and passwords (seperated by commas). Ex: `python geth_account_setup.py node1,node2,node3 pass1,pass2,pass3` if less passwords are given than nodes then the last password given will be used for the remaining nodes.
2. This will make directories for each node as well as an electric company node and a faucet node by default. These directories have the accounts wallet address, key file path, password, and validator status saved in seperate text files
3. The electric companies defualt password is 'electricity' and the faucet's is 'money'
4. The output will contain the nodes wallet address and key file name
### TODO: 
* This probably should be optimized for easier set up, such as the only arg it takes is the amount of nodes you want created

## Make the Genesis file 
1. run the `make_genesis.py` file passing at least node you want as a validator, the chain id number of your choice, and then optionally any accounts you want to be faucets (the default faucet will automatically be used). Ex: `python make_genesis.py node1,node2 1337` the faucet account will auto be passed so it isnt required. The node names need to be the same as their directory names/ the name given in the last section 
2. This should result in genesis.json file where the validators wallet are added to the extra data section, each validator, faucet and electric company node is pre-allocated with eth, and a timestamp of when the genesis file was created.
### TODO:
* probably dont need the faucet passing at all we should only need 1 faucet and that is already auto created so may as well auto allocate eth to it

## Initialize Geth nodes to genesis file
1. run the `init_geth.py` file with no arguments, `python init_geth.py`. 
2. This will print out the nodes it is initializing with the genesis file

## Create the bootnode
1. run the `create_bootnode.py` file with no arguments, `python create_bootnode.py`.
2. This will print the enode, make a boot.key file, and make an enode.txt file containing the enode

## Run the nodes
1. run the `run_nodes.py` file with the chain id used earlier as an argument. Ex: `python run_nodes.py 1337`
2. this will start up the bootnode and then the other nodes in seperate threads and print the  ports used for each node
3. To monitor a node in a seperate terminal use `geth attach http://127.0.0.1:<PORT>` use the last port number given from the 3 to attach to that node. The node needs to be a signer node though not sure why (electric company and faucet are signers automatically). For a list of commands: https://ethereum.stackexchange.com/questions/28703/full-list-of-geth-terminal-commands

### TODO
* probably should just have the chain id saved from the make_genesis.py step as well as randomly generated 
* need to make it where upon connecting each node requests 100 eth from the faucet node one time so they have enough eth to pay for the gas on transactions