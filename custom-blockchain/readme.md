This is a simple local network blockchain.

# How To Use
` python node.py <port> <name> <peer_port1> <peer_port2> ...`

Run the program in 3 seperate terminals matching the peers ports

The program will send blocks to the chain and store it in blockchain.db

# TODO

Next going to work on making a bootstrap node that will keep a list of those connected to the network so when a new node joins they only need to know the connection info for that node. Once one connects the new list of peers is sent out to all nodes so everyone has an updated list