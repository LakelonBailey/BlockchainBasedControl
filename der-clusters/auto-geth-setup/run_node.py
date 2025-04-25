import subprocess
import os
import sys
import requests


def start_nodes(port1, networkid, authourity=False):
    # start the node by first gathering the needed flags
    with open(f"/app/auto-geth-setup/geth_node/address.txt", "r") as file:
        address = file.read()
    password = f"/app/auto-geth-setup/geth_node/password.txt"
    datadir = f"/app/auto-geth-setup/geth_node/data"
    config = f"/app/auto-geth-setup/geth_node/data/config.toml"
    # need the ip for --nat flag
    try:
        response = requests.get("https://ifconfig.me")
        public_ip = response.text.strip()
        print(f"IP: {public_ip}")
    except requests.RequestException as e:
        print(f"Error getting public IP: {e}")
    #print(public_ip)
    command = []
    # geth --datadir data/ --unlock 0x704297Cd8FDB39cb7695462D8c431F8Cca3ec7Ca --password password.txt
    # --allow-insecure-unlock --port 30301 --http --http.api "web3,admin,net,eth,personal,miner"
    # --http.port 8586 --http.addr 0.0.0.0 --nat extip:134.209.41.49 --ws --ws.addr 0.0.0.0
    # --ws.port 30308 --authrpc.port 8551 --authrpc.addr 0.0.0.0 --networkid=26259
    # --nodiscover --config config.toml --mine
    # --miner.etherbase=0x704297Cd8FDB39cb7695462D8c431F8Cca3ec7Ca
    if authourity:
        command = [
            "geth",
            "--datadir",
            str(datadir),
            "--unlock",
            str(address),
            "--password",
            str(password),
            "--allow-insecure-unlock",
            "--port",
            str(port1),  # THIS NEEDS TO BE THE SAME PORT AS DEFINED IN THE ENODE
            "--http",
            "--http.api",
            '"web3,admin,net,clique,eth,personal,miner"',
            "--nat",
            f"extip:{public_ip}",
            f"--networkid={networkid}",
            "--nodiscover",
            "--config",
            str(config),
            "--mine",
            f"--miner.etherbase={address}",
        ]
    else:
        command = [
            "geth",
            "--datadir",
            str(datadir),
            "--unlock",
            str(address),
            "--password",
            str(password),
            "--allow-insecure-unlock",
            "--port",
            str(port1),  # THIS NEEDS TO BE THE SAME PORT AS DEFINED IN THE ENODE
            "--http",
            "--http.api",
            '"web3,admin,net,eth,personal,miner"',
            "--nat",
            f"extip:{public_ip}",
            "--ws",
            f"--networkid={networkid}",
            "--nodiscover",
            "--config",
            str(config),
        ]
    for c in command:
        print(c, end=" ")
    print()
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
      print(f"[GETH]: {line.strip()}")

    exit_code = proc.wait()
    print(f"[GETH exited with code {exit_code}]")


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python run_node.py port1 networkid \
is_authority(y/n)"
        )
        exit()
    port1 = sys.argv[1]
    network_id = sys.argv[2]
    is_auth = False
    if len(sys.argv) == 4:
        if sys.argv[3].lower() in ["y", "yes"]:
            is_auth = True
    start_nodes(port1, network_id, is_auth)


if __name__ == "__main__":
    main()
