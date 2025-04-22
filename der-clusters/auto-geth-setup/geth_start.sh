#!/bin/bash
uvicorn src.simulation.smart-meter:app --host 0.0.0.0 --port 8000 & sleep 5 && python3 -m src.simulation.device-collection --num-devices 20