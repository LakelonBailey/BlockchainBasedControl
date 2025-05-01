#!/usr/bin/env bash

# fallback to 8000 if METER_PORT isn't set
PORT="${METER_PORT:-8000}"
export METER_PORT="$PORT"

# fallback to 20 if NUM_DEVICES isn't set
NUM_DEVICES="${NUM_DEVICES:-20}"
export NUM_DEVICES

# fallback to 50:50 if CONSUMPTION_PRODUCTION_RATIO isn't set
CONSUMPTION_PRODUCTION_RATIO="${CONSUMPTION_PRODUCTION_RATIO:-50:50}"
export CONSUMPTION_PRODUCTION_RATIO

echo "🛰  Starting smart-meter on port $PORT"
uvicorn src.simulation.smart-meter:app --host 0.0.0.0 --port "$PORT" &

# give the server a moment to come up
sleep 5

echo "🔌  Launching device-collection ($NUM_DEVICES devices, ratio $CONSUMPTION_PRODUCTION_RATIO) against port $PORT"
python3 -m src.simulation.device-collection \
    --num-devices "$NUM_DEVICES" \
    --consumption-production-ratio "$CONSUMPTION_PRODUCTION_RATIO"
