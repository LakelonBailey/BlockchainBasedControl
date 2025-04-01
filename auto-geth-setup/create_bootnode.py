import subprocess
import os
import time
import re

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

if stdout:
  match = re.search(r'enode://([a-fA-F0-9]{128})', stdout)
  if match:
    enode_url = match.group(0)  # This will get the full enode URL
    print("Bootnode enode:", enode_url)
    with open('enode.txt', 'w') as file:
      file.seek(0)
      file.truncate()
      file.write(f'{enode_url}@127.0.0.1:0?discport=30301')
  else:
    print("No enode found in bootnode output.")
print("Bootnode created.")

  
  