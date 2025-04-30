from django.urls import path
from api.consumers import MeterStatusConsumer

websocket_urlpatterns = [
    path("meters/status/", MeterStatusConsumer.as_asgi()),
]
