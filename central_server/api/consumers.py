from lib.consumers import BaseConsumer
from channels.layers import get_channel_layer


class MeterStatusConsumer(BaseConsumer):
    message_types = ["meter_status"]

    async def connect(self):
        await super().connect()

        self.group_name = "meter_status"
        self.channel_layer = get_channel_layer()
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"MeterStatusConsumer joined group {self.group_name}")

    async def disconnect(self, close_code: int):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await super().disconnect(close_code)

    async def meter_status(self, event):
        data = event.get("data", {})
        await self.send_json(
            {
                "type": "meter_status",
                "data": data,
            }
        )
