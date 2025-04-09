import subprocess
import os
import time
import re
abs_dir = os.path.dirname(os.path.abspath(__file__))
def main():
  abs_dir = os.path.dirname(os.path.abspath(__file__))
  if os.path.exists('boot.key'):
    os.remove('boot.key')

  subprocess.run('bootnode -genkey boot.key', shell=True)

  bootnode_process = subprocess.Popen(
    ['bootnode', '-nodekey','boot.key','-verbosity', '7','-addr', "127.0.0.1:30301"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
  )

  time.sleep(1)


  bootnode_process.terminate()  # Gracefully terminate the bootnode
  bootnode_process.wait()  # Wait for the process to end
  stdout, stderr = bootnode_process.communicate()
  print('stdout:', stdout)
  if stdout:
    match = re.search(r'enode://([a-fA-F0-9]{128})', stdout)
    if match:
      enode_url = match.group(0)  # This will get the full enode URL
      print("Bootnode enode:", enode_url)
      if os.path.exists(f'{abs_dir}/enode.txt'):
        os.remove(f'{abs_dir}/enode.txt') #idk but sometimes it wouldnt write over the old enode file
      with open(f'{abs_dir}/enode.txt', 'w') as file:
        file.seek(0)
        file.truncate()
        file.write(f'{enode_url}@127.0.0.1:0?discport=30301')
    else:
      print("No enode found in bootnode output.")
  print("Bootnode created.")

if __name__ == "__main__":
  main()