import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import authenticate
from django.http import HttpRequest


class BaseConsumer(AsyncWebsocketConsumer):
    message_types = []

    def get_param(self, param: str):
        return self.scope["url_route"]["kwargs"].get(param, None)

    async def connect(self):
        # Initially, the connection is not authenticated.
        self.authenticated = False
        await self.accept()

    async def send_json(self, data: dict):
        return await self.send(text_data=json.dumps(data))

    async def disconnect(self, close_code: int):
        print(f"{self.__class__.__name__} disconnected with code: {close_code}")

    @database_sync_to_async
    def authenticate(self, token: str):
        http_request = HttpRequest()
        http_request.META["HTTP_AUTHORIZATION"] = f"Bearer {token}"
        return authenticate(request=http_request)

    async def receive(self, text_data: str):
        data = json.loads(text_data)
        message_type = data.get("type")
        print(f"{self.__class__.__name__} - Message received: {message_type}")

        # If not authenticated, only allow an "auth" message.
        if not self.authenticated:
            if message_type != "auth":
                await self.send_json({"type": "error", "detail": "Not authenticated."})
                await self.close()
                return

        # Process ping messages immediately.
        if message_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))
            print(f"{self.__class__.__name__} responded with pong")
        else:
            await self.run_handler(message_type, data)

    async def run_handler(self, message_type: str, data: dict):
        # Allow "auth" messages even if not part of the normal message_types.
        if message_type != "auth" and message_type not in self.message_types:
            raise ValueError(
                f"{self.__class__.__name__}: Invalid message type received: \
{message_type}"
            )

        handler = getattr(self, message_type, None)
        if handler is None:
            raise ValueError(
                f"{self.__class__.__name__}: No handler implemented for message type: \
{message_type}"
            )
        await handler(data)

    async def auth(self, data: dict):
        token = data.get("token")
        if not token:
            await self.send_json({"type": "auth_failure", "detail": "Token missing."})
            await self.close()
            return

        user = await self.authenticate(token)
        if user and user.is_authenticated:
            self.scope["user"] = user
            self.authenticated = True

            # Once authenticated, send "ready" to indicate that the connection is fully
            # set up.
            await self.send_json({"type": "ready"})
        else:
            await self.send_json({"type": "auth_failure", "detail": "Invalid token."})
            await self.close()
