import subprocess
import re
import sys
import string
import os
import json
import time
import shutil

def create_geth_account(nodes: list, passwords: list, node_pass_dict: dict):
  for node in nodes:
    node_dir = os.path.join(os.getcwd(), node)
    os.makedirs(node_dir, exist_ok=True)
    
    password_file = os.path.join(node_dir, "password.txt")
    with open(password_file, "w") as file:
      file.write(node_pass_dict[node])
    
    command = f'geth account new --datadir "{node_dir}/data" --password "{password_file}"'
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    match_eth_address = re.search(r"0x[a-fA-F0-9]{40}", result.stdout)
    if match_eth_address:
      eth_address = match_eth_address.group(0)
      print(f"{node} : {eth_address}")
    else:
      print("Error: couldn't extract eth address.")
      return
    address_file = os.path.join(node_dir, "address.txt")
    with open(address_file, "w") as file:
      file.write(eth_address)
      
    keystore_dir = os.path.join(node_dir, "data/keystore")
    key_files = [f for f in os.listdir(keystore_dir) if f.startswith("UTC--")]
    if key_files:
      key_file_name = key_files[0]
      print(f'{node} : {key_file_name}')
    else:
      print("Error: couldn't extract key file name.")
      return
    key_file = os.path.join(node_dir, "key.txt")
    with open(key_file, "w") as file:
      file.write(f'data/keystore/{key_file_name}')
    is_validator_file_path = os.path.join(node_dir, "validator.txt")
    with open(is_validator_file_path, 'w') as file:
      file.write('N')


#print(f"args: {len(sys.argv)}")

if len(sys.argv) != 3:
  print(f'USAGE: python geth_account_setup.py <node_name1>,<node_name2>,... <password1>,<password2>,...\n!!!Pass at least 1 node name and password, no spaces between the names or passwords, seperated by commas. if less passwords are given then nodes then the last password given will be used for the remaining nodes!!!')
  exit(1)

nodes = sys.argv[1].split(',')
passwords = sys.argv[2].split(',')
#signing_node_count = int(sys.argv[3])
if len(passwords) < len(nodes):
  while True:
    passwords.append(passwords[-1])
    if len(passwords) == len(nodes):
      break

if len(passwords) > len(nodes):
  while True:
    passwords.pop()
    if len(passwords) == len(nodes):
      break
nodes.append('electric_company')
passwords.append('electricity')
nodes.append('faucet1')
passwords.append('money')
#if signing_node_count > len(nodes):
  #signing_node_count = len(nodes)

  
    
print(f'nodes:         {nodes}')
print(f'passwords:     {passwords}')
#print(f'signing nodes: {signing_nodes}')

node_pass_dict = dict(zip(nodes, passwords))
for node in nodes:
  if os.path.isdir(node):
    shutil.rmtree(f'{node}')

create_geth_account(nodes, passwords, node_pass_dict)
#make_genesis_file(signing_nodes, 1234)


"""
TODO 
✅need to pass <node_name> as command line arg ☑
✅ geth --datadir '.<node_name>/data' account new --password <(echo "yourpassword") will auto make account ✔✔✔✔
✅need to save password and ethereum address to there own text file in the <node_name> dir
✅may need a script to reinitialize the genesis file
need to set up faucet account
after that move on to working as subprocess
"""