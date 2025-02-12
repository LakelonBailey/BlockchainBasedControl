# Base Image
FROM python:3.12

# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt first (optimizing Docker cache)
COPY requirements.txt /app/

# Install dependencies globally
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app/

# Expose Smart Meter WebSocket port
EXPOSE 8000

# Run both the Smart Meter and Device Collection as modules
CMD ["sh", "-c", "uvicorn src.simulation.smart-meter:app --host 0.0.0.0 --port 8000 & python -m src.simulation.device-collection --devices SmallSolarPanel,LEDLight,DesktopComputer --meter-origin=ws://localhost:8000 && wait"]
