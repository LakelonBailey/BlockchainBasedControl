FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies, Python, and pip
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    software-properties-common \
    tar \
    ca-certificates \
    python3 \
    python3-pip
#RUN echo "deb [trusted=yes] https://gethstore.blob.core.windows.net/builds/ubuntu/ $(lsb_release -cs) main" > /etc/apt/sources.list.d/ethereum.list
#RUN apt-get update && apt-get install -y bootnode && rm -rf /var/lib/apt/lists/*
# download and extract geth
WORKDIR /usr/local/bin
# add eth ppa and install bootnode
RUN add-apt-repository -y ppa:ethereum/ethereum \
    && apt-get update \
    && apt-get install -y bootnode \
    && rm -rf /var/lib/apt/lists/*

RUN wget https://gethstore.blob.core.windows.net/builds/geth-linux-amd64-1.13.14-2bd6bd01.tar.gz \
  && tar -xvzf geth-linux-amd64-1.13.14-2bd6bd01.tar.gz \
  && cp geth-linux-amd64-1.13.14-2bd6bd01/geth . \
  && rm -rf geth-linux-amd64-1.13.14-2bd6bd01* \
  && chmod +x geth
# Set working directory inside the container
WORKDIR /app

# Copy requirements.txt first (optimizing Docker cache)
COPY requirements.txt /app/

# Install dependencies globally
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app/
COPY auto-geth-setup/geth_start.sh ./geth_start.sh
RUN chmod +x ./geth_start.sh

# Expose Smart Meter WebSocket port
EXPOSE 8000

# Run both the Smart Meter and Device Collection as modules
CMD ["./geth_start.sh"]

