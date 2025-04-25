#!/usr/bin/env bash
# fallback to 8000 if METER_PORT isn't set
PORT="${METER_PORT:-8000}"
export METER_PORT="$PORT"

echo "🛰  Starting smart-meter on port $PORT"
uvicorn src.simulation.smart-meter:app --host 0.0.0.0 --port "$PORT" &

# give the server a moment to come up
sleep 5

echo "🔌  Launching device-collection (20 devices) against port $PORT"
python3 -m src.simulation.device-collection --num-devices 20
