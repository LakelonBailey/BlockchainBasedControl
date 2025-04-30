import os
import argparse
import subprocess
import sys
import yaml
import requests
from dotenv import load_dotenv


def fetch_client_credentials(
    central_server_origin: str, registration_token: str
) -> list[dict]:
    url = f"{central_server_origin}/api/register/"  # Change this if needed
    response = requests.post(url, json={"registration_token": registration_token})
    if response.status_code != 200:
        print("Failed to fetch credentials:", response.text)
        sys.exit(1)
    data = response.json()
    return data["clients"]


def build_compose_yaml(
    clients,
    central_server_origin,
    base_port,
    chain_id,
    auth_node_enodes,
    contract_abi_path,
    contract_address,
    disable_blockchain,
):
    services = {}
    for i, client in enumerate(clients, start=1):
        geth_port = 30303 + i  # port the geth node is broadcasting
        http_port = 8545 + i  # http geth console port 8545 + der cluster number
        auth_rpc_port = 20900 + i  # just need to define to prevent port conflicts
        ws_port = 22000 + i  # just need to define to prevent port conflicts
        name = f"der-cluster-{i}"
        services[name] = {
            "build": {"context": ".", "dockerfile": "Dockerfile"},
            "container_name": name,
            "network_mode": "host",
            # "networks": ["smart_grid"],
            "environment": [
                f"METER_ORIGIN=ws://localhost:{base_port + i}",
                f"METER_PORT={base_port + i}",
                f"CENTRAL_SERVER_ORIGIN={central_server_origin}",
                f"CLIENT_ID={client['client_id']}",
                f"CLIENT_SECRET={client['client_secret']}",
                f"CHAIN_ID={chain_id}",
                f"G_PORT={geth_port}",
                f"HTTP_PORT={http_port}",
                f"AUTH_RPC_PORT={auth_rpc_port}",
                f"WS_PORT={ws_port}",
                f"AUTH_ENODES={auth_node_enodes}",
                f"DISABLE_BLOCKCHAIN={str(disable_blockchain).lower()}",
                f"CONTRACT_ABI_PATH={contract_abi_path}",
                f"CONTRACT_ADDRESS={contract_address}",
            ],
        }

    return {
        "version": "3.8",
        "services": services,
        # "networks": {"smart_grid": {"driver": "bridge"}},
    }


def run_docker_compose(compose_dict: dict, stop: bool = False):
    yaml_bytes = yaml.dump(compose_dict).encode("utf-8")
    command = (
        ["docker", "compose", "-f", "-", "down"]
        if stop
        else ["docker", "compose", "-f", "-", "up", "--build", "-d"]
    )

    try:
        subprocess.run(command, input=yaml_bytes, check=True)
    except subprocess.CalledProcessError as e:
        print("Docker Compose failed:", e)
        sys.exit(1)


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description="Launch or stop DER clusters using a registration token"
    )
    parser.add_argument("registration_token", type=str, help="Registration token")
    parser.add_argument(
        "--chain-id",
        type=int,
        help="chain id number for your chain",
        default=os.environ.get("CHAIN_ID", None),
    )
    parser.add_argument(
        "--contract-abi-path",
        type=int,
        help="Contract ABI Path",
        default=os.environ.get("CONTRACT_ABI_PATH", None),
    )
    parser.add_argument(
        "--contract-address",
        type=int,
        help="Contract address",
        default=os.environ.get("CONTRACT_ADDRESS", None),
    )

    parser.add_argument(
        "--central-server-origin",
        default=os.environ.get("CENTRAL_SERVER_ORIGIN", "http://localhost:8000"),
        help="Origin URL for the central server",
    )
    parser.add_argument(
        "--auth-node-enodes",
        type=str,
        default=os.environ.get("AUTH_ENODES", None),
        help="Enodes of authourity nodes comma seperated, no spaces",
    )
    parser.add_argument(
        "--base-port",
        type=int,
        default=int(os.environ.get("BASE_METER_PORT", 8001)),
        help="Base port number for cluster port mapping",
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop the running DER cluster containers"
    )
    parser.add_argument(
        "--disable-blockchain",
        action="store_true",
        help="Prevents light nodes from being created and only simulates the devices.",
    )
    args = parser.parse_args()
    if not args.disable_blockchain:
        if args.chain_id is None and not args.disable_blockchain:
            raise ValueError(
                "Missing chain id! Pass as argument or declare as CHAIN_ID env var."
            )
        if args.auth_enodes is None:
            raise ValueError(
                "Missing auth enodes! Pass as argument or declare as AUTH_ENODES env var."
            )
        if args.contract_abi_path is None:
            raise ValueError(
                "Missing contract abi path! Pass as argument or declare as CONTRACT_ABI_PATH env var."
            )
        if args.contract_address is None:
            raise ValueError(
                "Missing contract address! Pass as argument or declare as CONTRACT_ADDRESS env var."
            )

    clients = fetch_client_credentials(
        args.central_server_origin, args.registration_token
    )
    compose_dict = build_compose_yaml(
        clients,
        args.central_server_origin,
        args.base_port,
        args.chain_id,
        args.auth_node_enodes,
        args.contract_abi_path,
        args.contract_address,
        args.disable_blockchain,
    )
    run_docker_compose(compose_dict, stop=args.stop)


if __name__ == "__main__":
    main()
