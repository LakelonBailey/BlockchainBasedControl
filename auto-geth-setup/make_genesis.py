import json
import sys
import time
import os

def make_genesis_file(signing_nodes : list, chainid : int, faucets: list):
  
  signing_address = ""
  alloc_addr = []
  for node in signing_nodes:
    with open(f'{node}/address.txt', 'r') as file:
      file_read = file.read()[2:].lower()
      print(f'{node}: {file_read}')
      alloc_addr.append(file_read)
      signing_address += file_read
  #for faucet in faucets:
    #alloc_addr.append(faucet)
  extra_data = '0x' + '0' * 64 + signing_address + '0' * 130
  hex_timestamp = hex(int(time.time()))
  print(hex_timestamp)
  print(extra_data)
  print(alloc_addr)
  alloc = {addr: {"balance":"0x200000000000000000000000000000000000000000000000000000000000000"} for addr in alloc_addr}
  data = {
    "config": {
    "chainId": chainid,
    "homesteadBlock": 0,
    "eip150Block": 0,
    "eip150Hash": "0x0000000000000000000000000000000000000000000000000000000000000000",
    "eip155Block": 0,
    "eip158Block": 0,
    "byzantiumBlock": 0,
    "constantinopleBlock": 0,
    "petersburgBlock": 0,
    "istanbulBlock": 0,
    "clique": {
      "period": 5,
      "epoch": 30000
    }
  },
  "nonce": "0x0",
  "timestamp": hex_timestamp,
  "extraData": extra_data,
  "gasLimit": "0x47b760",
  "difficulty": "0x1",
  "mixHash": "0x0000000000000000000000000000000000000000000000000000000000000000",
  "coinbase": "0x0000000000000000000000000000000000000000",
  "alloc": alloc 
  }
  
  with open('genesis.json', 'w') as file:
    file.seek(0)
    file.truncate()
    json.dump(data, file, indent=2)
  
  
  
    


if len(sys.argv) < 3:
  print(f'USAGE: python make_genesis.py <signing_node1>,<signing_node2>,... chainid, <faucetAccount1>,...\nEnter the signing signing node names (need to be the same names used in geth_account_setup.py) seperated by commas no spaces. then the chain id')
  exit(1)
nodes = sys.argv[1].split(',')
if 'electric_company' not in nodes:
  nodes.append('electric_company')
if 'faucet1' not in nodes:
  nodes.append('faucet1')
chain_id = int(sys.argv[2])
print(nodes)
faucets=[]
if len(sys.argv) == 4:
  faucets = sys.argv[3].split(',')
if 'electric_company' not in faucets:
  faucets.append('electric_company')
if 'faucet1' not in faucets:
  faucets.append('faucet1')

  
for node in nodes:
  if os.path.isdir(node) == False:
    print(f'Error: The signing node, {node}, is not a currently existing node. Exiting...')
    exit(1)
for faucet in faucets:
  if os.path.isdir(faucet) == False:
    print(f'Error: The faucet node: {faucet} is not a currently existing node. Exiting...')
    exit(1)
for node in nodes:
  valid_file = os.path.join(os.getcwd(), f'{node}/validator.txt')
  with open(valid_file, 'w') as file:
    file.seek(0)
    file.truncate()
    file.write('Y')
  
make_genesis_file(nodes, chain_id, faucets)