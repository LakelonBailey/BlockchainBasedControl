import os
import subprocess
import requests
import sys

"""
This will initialize the node in geth_node with the genesis file
This also assumes the genesis file will be called "genesis.json"
For nodes to peer with eachother they will compare the genesis file they
were initialized on.
This will also get the enode and write it to enode.txt for the node
"""
def init_geth(port):
  #set up the directory pathing
  abs_dir = os.path.dirname(os.path.abspath(__file__))
  node_dir = f'{abs_dir}/geth_node'
  data_dir = f'{abs_dir}/geth_node/data'
  print(node_dir)
  
  #initialize the node with geth init
  result = subprocess.run(f'geth --datadir {data_dir} init {abs_dir}/genesis.json', shell=True, capture_output=True, text=True)
  if result.returncode == 0:
    print('Successfully initialized the geth node')
  
  #craft the enode the format is:
  #enode://<unique_enode_value>@<public_ip>:<port>?discport=0
  #request ifconfig.me to get public 
  #NEED TO PASS THE PORT AS AN ARG SINCE PORTS CANT OVERLAP
  #SAME AS --port FLAG WHEN STARTING GETH
  #need to pass the ip as --nat extip:<public_ip>
  try:
    response = requests.get('https://ifconfig.me')
    public_ip = response.text.strip()
    print(f"IP: {public_ip}")
  except requests.RequestException as e:
    print(f'Error getting public IP: {e}')
  nodekey_file = os.path.join(data_dir, "geth/nodekey")
  print(nodekey_file)
  enode_cmd_result = subprocess.run(f"bootnode -nodekey {nodekey_file} -writeaddress", capture_output=True, text=True, check=True, shell=True)
  enode = f"enode://{enode_cmd_result.stdout.strip()}@{public_ip}:{port}?discport=0"
  print(f"enode: {enode}")
  enode_file = os.path.join(node_dir, "enode.txt")
  with open(enode_file, "w") as file:
    file.write(enode)
  
def main():
  if len(sys.argv) != 2:
    print(f"USAGE: python init_geth.py <port>")
    exit(1)
  abs_dir = os.path.dirname(os.path.abspath(__file__))
  genesis_file = "genesis.json"
  if os.path.exists(f'{abs_dir}/{genesis_file}') == False:
    print(f'Genesis file can not be found. the file should be named genesis.json and in the dir: {abs_dir}')
    exit(1)
  init_geth(str(sys.argv[1]))

if __name__ == "__main__":
  main()  
