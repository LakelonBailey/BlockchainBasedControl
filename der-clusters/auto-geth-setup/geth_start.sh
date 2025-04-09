#!/bin/bash
ARG1=$NUM_NODES
ARG2=$NUM_VAL_NODES
ARG3=$CHAIN_ID
uvicorn src.simulation.smart-meter:app --host 0.0.0.0 --port 8000 &
sleep 5
python3 -m src.simulation.device-collection --num-devices 20 &
#python3 ./auto-geth-setup/geth_account_setup.py "$ARG1"
#sleep 1
#python3 ./auto-geth-setup/make_genesis.py "$ARG2" "$ARG3"
#sleep 1
#python3 ./auto-geth-setup/init_geth.py
#sleep 1
#python3 ./auto-geth-setup/create_bootnode.py
#sleep 1
#python3 ./auto-geth-setup/run_nodes.py "$ARG3" &
tail -f /dev/null
#ARG1="$1"
#ARG2="$2"
#ARG3="$3"

#python3 geth_account_setup.py "$ARG1"
#sleep 1
#python3 make_genesis.py "$ARG2" "$ARG3"
#sleep 1
#python3 init_geth.py
#sleep 1
#python3 create_bootnode.py
#sleep 1
#python3 run_nodes.py "$ARG3" &
#tail -f /dev/null