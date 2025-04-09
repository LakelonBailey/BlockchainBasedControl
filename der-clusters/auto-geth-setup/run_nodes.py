import sys
import os
import subprocess
import time
import threading
abs_dir = os.path.dirname(os.path.abspath(__file__))
def get_sub_dirs():
  dir =  [f.path for f in os.scandir(f'{abs_dir}/geth_accounts/') if f.is_dir()]
  #for i in range(len(dir)):
    #dir[i] = dir[i][2:]
  return dir

def start_boot_node_process():
  bootnode_process = subprocess.Popen(
  ['bootnode', '-nodekey','boot.key','-verbosity', '7','-addr', "127.0.0.1:30301"],
  stdout=subprocess.DEVNULL,
  stderr=subprocess.DEVNULL,
  text=True,
  start_new_session=True
)
  return bootnode_process

def monitor_bootnode(process):
  try:
    while True:
      output = process.stdout.readline()
      if output == '' and process.poll() is not None:
        break
      if output:
        print(output.strip())
      time.sleep(.1)
  except KeyboardInterrupt:
    print('terminating process')
# Terminate the process 
  process.terminate()
  process.wait()
  print("Bootnode terminated.")

def start_nodes(node: str, port1: int, port2: int, port3: int, networkid: int):
  with open(f'{abs_dir}/enode.txt', 'r')as file:
    enode = file.read()
  print('------->',node)
  with open(f'{node}/address.txt', 'r') as file:
    address = file.read()
  
  password_file = f'{node}/password.txt'
  datadir = f'{node}/data'
  #print(datadir)
#signer node command
#geth --datadir "./data" --port 8500 --bootnodes enode://a7181617aceb7bd93254b976252558ebfa9e46cebd12c8c0fc93e7196bb8b71a8a6f927eb4a8b5a27477c4c06583ede7648804eed1adb416774e941351014f2b@127.0.0.1:0?discport=30301 
#--authrpc.port 30302 --ipcdisable --allow-insecure-unlock --http --http.corsdomain="*" --http.api web3,eth,debug,personal,net --networkid 53358 
# --unlock 0xbb932EC245C476C5645dA3F8a86d446a4F51Da00 --password password.txt --http.port 8499 -mine -miner.etherbase=0xbb932EC245C476C5645dA3F8a86d446a4F51Da00 
# --allow-insecure-unlock

#lite node
#geth --datadir "./data" --port 8504 --bootnodes enode://a7181617aceb7bd93254b976252558ebfa9e46cebd12c8c0fc93e7196bb8b71a8a6f927eb4a8b5a27477c4c06583ede7648804eed1adb416774e941351014f2b@127.0.0.1:0?discport=30301 
# --authrpc.port 30304 --networkid 53358 --unlock 0xAEaF64C8d2DBd8FD83093a306d2e7701F72442BC --password password.txt --http.api web3,eth,debug,personal,net --http.port 4898
  node_start_command_signer = [ 
    'geth',
    '--datadir', datadir,
    '--port', str(port1),
    '--bootnodes', enode,
    '--authrpc.port', str(port2),
    '--ipcdisable',
    '--allow-insecure-unlock',
    '--http',
    '--http.corsdomain="*"',
    '--http.api',
    'web3,eth,debug,personal,net,admin,clique',
    '--networkid', str(networkid),
    '--unlock', str(address),
    '--password', str(password_file),
    '--http.port', str(port3),
    '-mine',
    f'-miner.etherbase={address}',
    '--allow-insecure-unlock'
    ]
  node_start_lite = [
    'geth',
    '--datadir', datadir,
    '--port', str(port1),
    '--bootnodes', enode,
    '--authrpc.port', str(port2),
    '--networkid', str(networkid),
    '--unlock', str(address),
    '--password', str(password_file),
    "--http",
    '--http.api',
    'web3,eth,debug,personal,net,admin,clique',
    '--allow-insecure-unlock',
    '--http.port', str(port3),
    '--http.corsdomain="*"',
  ]
  node_dir = os.path.join(f'{abs_dir}/geth_accounts', node)
  validator_file = os.path.join(node_dir, "validator.txt")
  with open(validator_file, "r") as file:
    is_valid = file.read()
    if is_valid == 'Y':
      command = node_start_command_signer
    else:
      command = node_start_lite
  print(f'Starting Geth node: {node}, at using ports {port1}, {port2}, {port3}')
  subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True, start_new_session=True)
  """
  while True:
    output = process.stdout.readline()
    if output == "" and process.poll() is not None:
      break  # Stop if process ends
    if output:
      print(f"Geth Output: {output.strip()}")
    time.sleep(.2)
  process.wait()
  """
def main():
  abs_dir = os.path.dirname(os.path.abspath(__file__))
  if len(sys.argv) != 2:
    print('Usage: python run_nodes.py <chainid>')
    exit()
  nodes = get_sub_dirs()
  print(nodes)

  bootnode = start_boot_node_process()


  #monitor_bootnode_thread = threading.Thread(target=monitor_bootnode, args=(bootnode,))
  #monitor_bootnode_thread.start()
  time.sleep(2)
  threads = []
  port1 = 8400
  port2 = 30302
  port3 = 4898
  if len(sys.argv) == 3:
    port1 += int(sys.argv[2])
    port2 += int(sys.argv[2])
    port3 += int(sys.argv[2])
    
  chainid = int(sys.argv[1])
  #with open("chain_id.txt", "r") as f:
    #chainid = int(f.read().strip())
  #start_nodes(nodes[0], 8400, 30302, 4898, 8771)
  for node in nodes:
    start_nodes(node, port1, port2, port3, chainid)
    port1 += 1
    port2 += 1
    port3 += 1
  #monitor_bootnode_thread.join()
  #bootnode.terminate()
  #bootnode.wait()
if __name__ == "__main__":
  main()
