import argparse
import subprocess
import sys
import yaml
import requests


def fetch_client_credentials(central_server_origin, registration_token):
    url = f"{central_server_origin}/api/register/"  # Change this if needed
    response = requests.post(url, json={"registration_token": registration_token})
    if response.status_code != 200:
        print("Failed to fetch credentials:", response.text)
        sys.exit(1)
    data = response.json()
    return data["clients"]


def build_compose_yaml(clients, central_server_origin, base_port, num_nodes, num_val_nodes, chain_id):
    services = {}

    for i, client in enumerate(clients, start=1):
        name = f"der-cluster-{i}"
        services[name] = {
            "build": {"context": ".", "dockerfile": "Dockerfile"},
            "container_name": name,
            "networks": ["smart_grid"],
            "ports": [f"{base_port + i + 1}:3000"],
            "environment": [
                f"METER_ORIGIN=ws://{name}:{base_port}",
                f"CENTRAL_SERVER_ORIGIN="
                f"{central_server_origin.replace('localhost', 'host.docker.internal')}",
                f"CLIENT_ID={client['client_id']}",
                f"CLIENT_SECRET={client['client_secret']}",
                f"NUM_NODES={num_nodes}",
                f"NUM_VAL_NODES={num_val_nodes}",
                f"CHAIN_ID={chain_id}"
            ],
        }

    return {
        "version": "3.8",
        "services": services,
        "networks": {"smart_grid": {"driver": "bridge"}},
    }


def run_docker_compose(compose_dict, stop=False):
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
    parser = argparse.ArgumentParser(
        description="Launch or stop DER clusters using a registration token"
    )
    parser.add_argument(
        "registration_token", type=str, help="Registration token"
    )
    parser.add_argument(
      '--num_nodes', type=int, help='Amount of nodes for the blockchain'
    )
    parser.add_argument(
      '--val_nodes', type=int, help="Amount of validator nodes, must be greater than or equal to 2"
    )
    parser.add_argument(
      '--chain_id', type=int, help="chain id number for your chain"
    )
    parser.add_argument(
        "--central-server-origin",
        default="http://localhost:8000",
        help="Origin URL for the central server",
    )
    parser.add_argument(
        "--base-port",
        type=int,
        default=8000,
        help="Base port number for cluster port mapping",
    )
    parser.add_argument(
        "--stop", action="store_true", help="Stop the running DER cluster containers"
    )
    args = parser.parse_args()

    clients = fetch_client_credentials(
        args.central_server_origin, args.registration_token
    )
    compose_dict = build_compose_yaml(
        clients, args.central_server_origin, args.base_port, args.num_nodes, args.val_nodes, args.chain_id
    )
    run_docker_compose(compose_dict, stop=args.stop)


if __name__ == "__main__":
    main()
