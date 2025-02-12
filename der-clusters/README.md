# DER Clusters Simulation

## Overview

This project simulates **Distributed Energy Resource (DER) clusters**, where each cluster consists of a **smart meter WebSocket server** that interacts with connected **energy consumption and production devices** (e.g., solar panels, LED lights, computers, etc.).

Each cluster:

- Runs a **smart meter WebSocket server** that tracks energy transactions.
- Spawns **multiple simulated devices** that report energy consumption/production.
- Logs energy transactions in a structured format.

The project can be run **locally** or inside **Docker containers**.

---

## **1. Running a DER Cluster Locally**

### **Prerequisites**

Ensure you have the following installed:

- **Python 3.12+**
- **pip**

### **Installation**

1. Clone the repository:

   ```sh
   git clone https://github.com/your-repo/der-clusters.git
   cd der-clusters
   ```

2. Create a virtual environment:

   ```sh
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate     # Windows
   ```

3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```

### **Running the Smart Meter and Devices**

Start a single DER cluster locally with a set of devices:

```sh
uvicorn src.simulation.smart-meter:app --host 0.0.0.0 --port 8000 &
python -m src.simulation.device-collection --devices SmallSolarPanel,LEDLight,DesktopComputer --meter-origin=ws://localhost:8000
```

- The **smart meter** runs on port **8000**.
- The **devices** connect to the WebSocket endpoint and start reporting energy data.
- Logs are stored in **smart_meter.log** and displayed in the terminal.

To stop the simulation, press `CTRL+C`.

---

## **2. Running a DER Cluster with Docker**

### **Prerequisites**

Ensure you have the following installed:

- **Docker**
- **Docker Compose** (if using older Docker versions)

### **Building and Running Containers**

1. **Build the Docker image:**

   ```sh
   docker build -t der-cluster .
   ```

2. **Run a single cluster container:**
   ```sh
   docker run -p 8000:8000 --name der-cluster-1 der-cluster
   ```
   - The cluster will run a **smart meter WebSocket server** and start **devices**.
   - Logs are streamed to the container output.
   - You can stop the container using `CTRL+C` or:
     ```sh
     docker stop der-cluster-1
     ```

### **Running Multiple Clusters with Docker Compose**

To run multiple DER clusters as separate containers:

```sh
docker-compose up --build
```

This will:

- Start **three clusters** (`der-cluster-1`, `der-cluster-2`, `der-cluster-3`)
- Assign a **unique WebSocket port** to each cluster.
- Automatically restart services if needed.

To stop all clusters:

```sh
docker-compose down
```

---

## **3. Logs & Monitoring**

- **Device transactions** are logged in `smart_meter.log`.
- To view real-time logs of a running container:
  ```sh
  docker logs -f der-cluster-1
  ```
- To check connected devices:
  ```sh
  curl http://localhost:8000/devices
  ```
