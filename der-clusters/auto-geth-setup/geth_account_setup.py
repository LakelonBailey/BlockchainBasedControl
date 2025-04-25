import subprocess
import re
import os
import shutil
import secrets
import string
import time
"""
IF A NODE FOLDER IS ALREADY EXISTING THIS WILL DELETE IT
This will call the geth account new and save different information
about the node to txt files for easier access. Will all be stored
in a folder called geth_node
password.txt = password
address.txt  = nodes public ethereum key
key.txt      = name of the key file (is random) but needed to unlock account later
"""


def create_geth_account(password: str):
    # sets up the node directory
    node_dir = os.path.join('/app/auto-geth-setup/', f"geth_node/")
    os.makedirs(node_dir, exist_ok=True)

    # makes the password file
    password_file = os.path.join(node_dir, "password.txt")
    with open(password_file, "w") as file:
        file.write(str(password))
    print(password)
    # command to make the account via cmd line
    command = (
        f'geth account new --datadir "{node_dir}data" --password "{password_file}"'
    )
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    # checks for the eth public key address in output and
    # write it to address.txt file in the geth_node folder
    match_eth_address = re.search(r"0x[a-fA-F0-9]{40}", result.stdout)
    if match_eth_address:
        eth_address = match_eth_address.group(0)
        print(f"eth address: {eth_address}")
    else:
        print("Error: couldn't extract eth address.")
        return
    eth_address_file = os.path.join(node_dir, "address.txt")
    with open(eth_address_file, "w") as file:
        file.write(eth_address)

    # do the same thing as the address but for the key file name and
    # write it to key.txt in the geth_node folder
    keystore_dir = os.path.join(node_dir, "data/keystore")
    key_files = [f for f in os.listdir(keystore_dir) if f.startswith("UTC--")]
    if key_files:
        key_file_name = key_files[0]
        print(f"key file: {key_file_name}")
    else:
        print("Error: couldn't extract key file name.")
        return
    key_file = os.path.join(node_dir, "key.txt")
    with open(key_file, "w") as file:
        file.write(f"data/keystore/{key_file_name}")


# generate a random password
def generate_password(length=12, include_symbols=True):
    alphabet = string.ascii_letters + string.digits
    if include_symbols:
        alphabet += string.punctuation
    password = "".join(secrets.choice(alphabet) for i in range(length))
    return password


def main():
    if os.path.isdir(f"geth_node"):
        shutil.rmtree(f"geth_node")
    create_geth_account(generate_password())
    print("PLEASE BE FIRST")


if __name__ == "__main__":
    main()
