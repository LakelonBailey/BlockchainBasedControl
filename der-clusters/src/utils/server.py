import os
import time
import httpx

# Origin for the central server
CENTRAL_SERVER_ORIGIN = os.environ["CENTRAL_SERVER_ORIGIN"]


class CentralServerAPI:
    def __init__(self, client_id: str, client_secret: str, scope: str = None):
        self.access_token = None
        self.token_expires_at = 0
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.client = httpx.AsyncClient(base_url=CENTRAL_SERVER_ORIGIN)

    async def get_access_token(self):
        """
        Retrieves a valid access token using the client credentials grant
        asynchronously.
        """
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        payload = {"grant_type": "client_credentials"}
        if self.scope:
            payload["scope"] = self.scope

        response = await self.client.post(
            "/o/token/", data=payload, auth=(self.client_id, self.client_secret)
        )
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            self.token_expires_at = time.time() + expires_in - 10  # Subtract a buffer
            return self.access_token
        else:
            raise Exception("Failed to obtain access token: " + response.text)

    async def post(self, url: str, payload: dict = None, headers: dict = None):
        if headers is None:
            headers = {}
        headers.update({"Authorization": f"Bearer {await self.get_access_token()}"})

        return await self.client.post(url, json=payload, headers=headers)

    async def put(self, url: str, payload: dict = None, headers: dict = None):
        if headers is None:
            headers = {}
        headers.update({"Authorization": f"Bearer {await self.get_access_token()}"})

        return await self.client.put(url, json=payload, headers=headers)

    async def get(self, url: str):
        headers = {"Authorization": f"Bearer {await self.get_access_token()}"}
        return await self.client.get(url, headers=headers)

    async def ping(self):
        """
        Ping the server to communicate uptime.
        """
        response = await self.post("/api/ping/")
        if response.status_code in (200, 201):
            return
        else:
            raise Exception("Failed to ping central server: " + response.text)

    async def create_transaction(self, order_id: str, transaction_payload: dict):
        payload = {"order_id": order_id, **transaction_payload}
        response = await self.post(
            "/api/transactions/",
            payload=payload,
            headers={
                "Content-Type": "application/json",
            },
        )
        if response.status_code in (200, 201):
            return response.json()
        else:
            raise Exception("Failed to create transaction: " + response.text)

    async def create_order(self, order_id: str, order_payload: dict):
        payload = {"order_id": order_id, **order_payload}
        response = await self.post(
            "/api/orders/",
            payload=payload,
            headers={
                "Content-Type": "application/json",
            },
        )
        if response.status_code in (200, 201):
            return response.json()
        else:
            raise Exception("Failed to create order: " + response.text)

    async def update_order(self, order_id: str, order_payload: dict):
        payload = {"order_id": order_id, **order_payload}
        response = await self.put(
            "/api/orders/",
            payload=payload,
            headers={
                "Content-Type": "application/json",
            },
        )
        if response.status_code in (200, 201):
            return response.json()
        else:
            raise Exception("Failed to update order: " + response.text)

    async def post_transactions(self, transactions: list[dict]):
        """
        Posts a batch of transactions to the central server asynchronously.
        Each transaction should be a dictionary with 'transaction_type' and
        'energy_kwh'.
        """
        payload = {"transactions": transactions}
        response = await self.post(
            "/api/transactions/batch_upload/",
            payload=payload,
            headers={
                "Content-Type": "application/json",
            },
        )
        if response.status_code in (200, 201):
            return response.json()
        else:
            raise Exception("Failed to post transactions: " + response.text)
