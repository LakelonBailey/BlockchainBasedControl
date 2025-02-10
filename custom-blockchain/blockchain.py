import sqlite3
import json
import time
import hashlib

class Blockchain:
    def __init__(self, db_path="blockchain.db"):
        self.db = db_path
        self.chain = []  # Blockchain stored in memory
        self.create_table()  # Ensure database table exists
        self.load_chain()  # Load blockchain from database

    def create_table(self):
        """Create blockchain table if it doesn't exist"""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS blocks
                     (block_index INTEGER PRIMARY KEY, timestamp TEXT, data TEXT, 
                      previous_hash TEXT, validator TEXT, signature TEXT, hash TEXT)''')
        conn.commit()
        conn.close()

    def load_chain(self):
        """Load the blockchain from the database"""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT * FROM blocks ORDER BY CAST(block_index AS INTEGER) ASC")
        rows = c.fetchall()

        for row in rows:
            block = {
                "index": row[0],
                "timestamp": row[1],
                "data": json.loads(row[2]),
                "previous_hash": row[3],
                "validator": row[4],
                "signature": row[5],
                "hash": row[6]
            }
            self.chain.append(block)

        conn.close()

        # Ensure genesis block exists
        if not self.chain:
            self.create_genesis_block()

    def create_genesis_block(self):
        """Create the first block (Genesis Block) if the chain is empty"""
        genesis_block = self.create_block("Genesis Block", "Admin", "0")
        print("Genesis Block Created:", genesis_block)

    def create_block(self, data, validator, previous_hash):
        """Create a new block and add it to the blockchain"""
        last_block = self.get_last_block()  # Fetch the latest block

        # If there's no previous block, create the genesis block
        if last_block is None:
            previous_hash = "0" * 64  # Standard genesis block hash
            index = 1  # Genesis block index
        else:
            previous_hash = last_block["hash"]
            index = last_block["index"] + 1  # Increment index correctly

        timestamp = str(int(time.time()))
        block_data = json.dumps(data)

        # Generate block hash
        block_string = f"{index}{timestamp}{block_data}{previous_hash}{validator}"
        block_hash = hashlib.sha256(block_string.encode()).hexdigest()

        block = {
            "index": index,
            "timestamp": timestamp,
            "data": data,
            "previous_hash": previous_hash,
            "validator": validator,
            "signature": "valid_signature",  # Placeholder for actual signing
            "hash": block_hash
        }

        # Add block to DB
        self.save_block(block)
        self.chain.append(block)
        print(f"Block Created: {block}")  # Debug print
        return block

    def save_block(self, block):
        """Save a new block to the database"""
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute('''INSERT INTO blocks (block_index, timestamp, data, previous_hash, validator, signature, hash) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (block["index"], block["timestamp"], json.dumps(block["data"]),
                   block["previous_hash"], block["validator"], block["signature"], block["hash"]))
        conn.commit()
        conn.close()
    def get_last_block(self):
      conn = sqlite3.connect(self.db)
      c = conn.cursor()
      c.execute("SELECT * FROM blocks ORDER BY CAST(block_index AS INTEGER) DESC LIMIT 1")  # Get the latest block
      row = c.fetchone()
      conn.close()

      if row:
          return {
              "index": row[0],
              "timestamp": row[1],
              "data": json.loads(row[2]),
              "previous_hash": row[3],
              "validator": row[4],
              "signature": row[5],
              "hash": row[6]
          }
      return None  # No blocks exist yet
    
    def validate_block(self, block):
        """Validate a block before adding it to the blockchain"""
        if len(self.chain) == 0:  # First block must be the Genesis Block
            return block["previous_hash"] == "0"

        last_block = self.get_last_block()

        # Check block index
        if block["index"] != last_block["index"] + 1:
            print(f"Invalid block index\n block[index] == {block['index']}\n last_block[index] == {last_block['index']}")
            return False

        # Check previous hash
        if block["previous_hash"] != last_block["hash"]:
            print("Invalid previous hash")
            return False

        # Recalculate hash
        block_string = f"{block['index']}{block['timestamp']}{json.dumps(block['data'])}{block['previous_hash']}{block['validator']}"
        recalculated_hash = hashlib.sha256(block_string.encode()).hexdigest()

        if block["hash"] != recalculated_hash:
            print(f"Invalid block hash\n block[hash] == {block['hash']}\n recalculated_hash == {recalculated_hash}")
            return False

        print(f"Block Validated: {block}")  # Debug print
        return True


