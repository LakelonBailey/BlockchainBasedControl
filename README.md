# Blockchain Based Control

## General Setup

1. Clone the repository: `git clone https://github.com/LakelonBailey/BlockchainBasedControl`
2. Move to the root directory: `cd BlockchainBasedControl`

## Local Simulation Setup

### Central Server

The central server must be set up before the DER clusters.

#### Preliminary steps:

1. Install PostgreSQL on your machine from the [website](https://www.postgresql.org/download/).
2. Create a local database and keep track of the `username`, `password`, `host`, `port`, and `database name`.

#### Setting up virtual environment:

1. Move to the central server folder: `cd central_server`
2. Create a python virtual environment: `python3 -m venv .venv`
3. Activate virtual environment:
   - **Mac OS/Linux:** `source .venv/bin/activate`
   - **Windows:** `.venv\Scripts\activate`
4. Install dependencies: `pip install -r requirements.txt`

#### Setting up local server:

1. Create a file called `.env` in the `central_server/` directory and add the following content:

```
ENVIRONMENT=local
SECRET_KEY=<Random secret key. Use https://randomkeygen.com to generate>
DB_NAME=<database name>
DB_USER=<database username>
DB_PASSWORD=<database password>
DB_HOST=<database host>
DB_PORT=<database port>
OIDC_RSA_PRIVATE_KEY_BASE64=<base64 encoded private key. Just ask ChatGPT how to generate this>
```

2. Run database migration to set database state: `python manage.py migrate`
3. Create a superuser for yourself: `python manage.py createsuperuser`
4. Run local server: `python manage.py runserver 8000`
5. Test that django setup worked properly by visiting `http://localhost:8000/admin` and logging in with your superuser credentials.

#### Adding a cluster registration token

1. Go to `http://localhost:8000/admin/api/clusterregistration/`
2. Click **Add Cluster Registration**
3. Fill out the form. For now, set the "Quantity" field to 3.
4. After creating the cluster registration, go to edit the same registration and copy the "Token" field.
5. You have now created a token that can be used to start a DER simulation. This token will be used in a later step.
6. Keep your server running and open a different terminal for the next steps. The central server has to be running for the DER simulation to work.

### DER Clusters

#### Preliminary setup

1. Install Docker Desktop on your machine from the [website](https://www.docker.com/products/docker-desktop/). Then, verify that it is running. This can be done by running `docker` in your terminal or by opening the Docker Desktop application.

#### Setting up the simulation environment

1. Move the the `der-cluster` folder from the root directory of the project.
2. Follow steps 2-4 of the **Setting up virtual environment** section of the central server setup. You are just creating a different virtual environment for the der cluster software, as it has different packages.

#### Running the simulation

1. With your virtual environment activated, simply try running `python launch_clusters.py --registration-token <token>` using the token you made above.
2. If all goes well, you should be able to run `docker ps` and see three containers running with the names `der-cluster-1`, `der-cluster-2`, and `der-cluster-3`. If you want to view the logs for one of these clusters, run `docker logs <container id> -f` using the container id you can see after running `docker ps`. The `-f` flag is telling docker to follow the log file stream.
3. To stop the simulation, run `python launch_clusters.py --registration-token <token> --stop` using the same token from above. Using the same registration token will cause the script to re-generate the same docker compose configuration again, which is crucial to ensure all containers are stopped.
4. If the containers are running properly, you should start to see some logs in your central server where they are uploading transaction batches and pinging the server regularly.
