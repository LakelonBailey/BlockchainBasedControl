import subprocess
import re
import sys
import os
import shutil

def create_geth_account(nodes: list, passwords: list, node_pass_dict: dict):
  for node in nodes:
    abs_dir = os.path.dirname(os.path.abspath(__file__))
    node_dir = os.path.join(abs_dir, f'geth_accounts/{node}')
    print(node_dir)
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
def main():
  if len(sys.argv) < 2:
    print(f'USAGE: python geth_account_setup.py <number of nodes of at least 2>')
    exit(1)
  if int(sys.argv[1]) < 1:
    print(f'USAGE: python geth_account_setup.py <number of nodes of at least 2, you input less than that>')
    exit(1)
  node_count = int(sys.argv[1])

  #passwords = sys.argv[2].split(',')
  #signing_node_count = int(sys.argv[3])\
  nodes = []
  passwords = []
  for i in range(node_count):
    node_num = i + 1
    nodes.append(f'node{node_num}')
    passwords.append(f'node{node_num}')
  if len(sys.argv) == 3:
    nodes = []
    nodes.append(f'node{sys.argv[2]}')
  if len(sys.argv) != 3:
    nodes.append('electric_company')
    passwords.append('electric_company')
    nodes.append('faucet1')
    passwords.append('faucet1')

  #if signing_node_count > len(nodes):
    #signing_node_count = len(nodes)

    
      
  print(f'nodes:         {nodes}')
  #print(f'signing nodes: {signing_nodes}')

  node_pass_dict = dict(zip(nodes, passwords))


  if os.path.isdir(f'geth_accounts') and len(sys.argv) != 3:
    shutil.rmtree(f'geth_accounts')
  create_geth_account(nodes, passwords, node_pass_dict)
  #make_genesis_file(signing_nodes, 1234)


if __name__ == "__main__":
  main()
