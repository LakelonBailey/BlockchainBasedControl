import os
import sys
import time
import re
import subprocess


def init_geth(nodes: list):
  for node in nodes:
    node_data_dir = node + '/data'
    #print(node_data_dir)
    print(f'initializing {node}')
    result = subprocess.run(f'geth --datadir {node_data_dir} init ./genesis.json', shell=True, capture_output=True, text=True)
    if result.returncode == 0:
      print(f'Succesfully initialized {node}')
 
def get_sub_dirs():
  dir =  [f.path for f in os.scandir('./') if f.is_dir()]
  for i in range(len(dir)):
    dir[i] = dir[i][2:]
  return dir

#if len(sys.argv) != 2:
  #print(f'!!!USAGE: python init_geth.py <node_name1>,<node_name2>,... This should be the 3rd program ran. Same node names no spaces as arg!!!')
  #exit(1)
#nodes = sys.argv[1].split(',')
nodes = get_sub_dirs()
print(nodes)
genesis_file = './genesis.json'
for node in nodes:
  if os.path.isdir(node) == False:
    print(f'Error: The node, {node}, is not a currently existing node. Exiting...')
    exit(1)
if os.path.exists(genesis_file) == False:
  print(f'Genesis file can not be found. Run make_genesis.py to create one. Exiting')
  exit(1)
init_geth(nodes)