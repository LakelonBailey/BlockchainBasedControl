import os
import subprocess

def init_geth(nodes: list):
  abs_dir = os.path.dirname(os.path.abspath(__file__))
  for node in nodes:
    
    node_data_dir = f'{node}/data'
    #print(node_data_dir)
    #input()
    print(f'initializing {node}')
    result = subprocess.run(f'geth --datadir {node_data_dir} init {abs_dir}/genesis.json', shell=True, capture_output=True, text=True)
    if result.returncode == 0:
      print(f'Succesfully initialized {node}')
 
def get_sub_dirs():
  abs_dir = os.path.dirname(os.path.abspath(__file__))
  dir =  [f.path for f in os.scandir(f'{abs_dir}/geth_accounts') if f.is_dir()]
  #for i in range(len(dir)):
    #dir[i] = dir[i][16:] #./geth_accounts/ is 16 chars
  return dir

def main():
  abs_dir = os.path.dirname(os.path.abspath(__file__))
  
  #if len(sys.argv) != 2:
    #print(f'!!!USAGE: python init_geth.py <node_name1>,<node_name2>,... This should be the 3rd program ran. Same node names no spaces as arg!!!')
    #exit(1)
  #nodes = sys.argv[1].split(',')
  nodes = get_sub_dirs()
  #input('get_sub_dirs end')
  #print(nodes)
  genesis_file = './genesis.json'
  for node in nodes:
    print(node)
    #input()
    #print(abs_dir)
    #print(f'node-------> {node}')
    node_dir = os.path.join(abs_dir, f'geth_accounts/')
    if os.path.isdir(f'{node}') == False:
      print(f'Error: The node, {node}, is not a currently existing node. Exiting...')
      exit(1)
  if os.path.exists(f'{abs_dir}/{genesis_file}') == False:
    print(f'Genesis file can not be found. Run make_genesis.py to create one. Exiting')
    exit(1)
  print(nodes)
  init_geth(nodes)
  
if __name__ == "__main__":
  main()
