import socket
import json
from blockchain import Blockchain  # Import your blockchain logic
import sys
import threading


class Node:
  def __init__(self, name, host, port, peers):
      self.name = name
      self.host = host
      self.port = port
      self.peers = peers  # List of peer node addresses
      self.blockchain = Blockchain()  # Load the blockchain

  def send_block(self, block):
      """Send a new block to all peer nodes"""
      block_data = json.dumps(block)  # Convert block to JSON
      for peer in self.peers:
          peer_host, peer_port = peer
          try:
              with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                  s.connect((peer_host, peer_port))
                  s.sendall(block_data.encode("utf-8"))
                  print(f"Block sent to {peer_host}:{peer_port}")
          except Exception as e:
              print(f"Failed to send block to {peer_host}:{peer_port} - {e}")

  def receive_block(self):
      """Listen for incoming blocks and add them to the blockchain"""
      with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
          server.bind((self.host, self.port))
          server.listen()
          print(f"Node listening on {self.host}:{self.port}")

          while True:
              conn, addr = server.accept()
              with conn:
                  data = conn.recv(4096).decode("utf-8")
                  if data:
                      block = json.loads(data)  # Convert JSON back to dictionary
                      print(f"Received block from {addr}: {block}")

                      # Validate and add the block to the blockchain
                      if self.port == 5000:
                        if self.blockchain.validate_block(block) and self.port == 5000:
                            self.blockchain.save_block(block)
                            print("Block added to the blockchain")
                        else:
                            print("Block validation failed")

  def create_and_send_block(self, data, validator):
    """Create a new block, add it to the blockchain, and broadcast it"""
    last_block = self.blockchain.get_last_block()
    previous_hash = last_block["hash"] if last_block else "0"

    new_block = self.blockchain.create_block(data, validator, previous_hash)
    self.send_block(new_block)  # Broadcast block to peers
    return new_block
  def start_sending_and_receiving(self):
    """ Start sending and receiving blocks in separate threads """
    # Start thread for receiving blocks
    receive_thread = threading.Thread(target=self.receive_block)
    receive_thread.daemon = True  # Daemonize to terminate with main program
    receive_thread.start()
    amount = 10
    # Send a block every 5 seconds (just an example)
    while True:
        # Example block data and validator
        #print("Press 's' to send a block, 'q' to quit\n")
        threading.Event().wait(1)
        user_in = input("Press 's' to send a block, 'q' to quit\n")
        if user_in == 'q':
          exit(0)
        if user_in == 's':
          reciver = str(input("Enter reciver name: "))
          amount = int(input("Enter amount: "))
          name = self.name
          new_block_data = {"sender": name, "receiver": reciver, "amount":amount}
          new_block_validator = "Validator1"
          #if self.port == 5000: #might need to remove this line
          self.create_and_send_block(new_block_data, new_block_validator)
          #amount += 1
        # Sleep for a while before sending another block
        #input("")
        #threading.Event().wait(5)
        



# Example Usage
if __name__ == "__main__":
  n = len(sys.argv)
  if n < 3:
      print("Usage: python node.py  <port> <name> <peer1> <peer2> ...")
      sys.exit(1)
  PORT = int(sys.argv[1])
  name = sys.argv[2]
  peers = []
  for i in range(3, n): 
    peers.append(("localhost", int(sys.argv[i])))
  print(peers)
  
  
  #peers = [("localhost", 5001), ("localhost", 5002)]  # Peer nodes
  node = Node(name, "localhost", PORT, peers)
  node.start_sending_and_receiving()
  # Example: Create a new block and send it
  """
  node.create_and_send_block(
      {"sender": "bob", "receiver": "alice", "amount": 100}, "Validator2"
  )

  # Start listening for incoming blocks
  node.receive_block()
"""