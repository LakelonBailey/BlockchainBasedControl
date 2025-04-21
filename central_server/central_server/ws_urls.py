from django.urls import re_path
from channels.routing import URLRouter
from api.ws_urls import websocket_urlpatterns as api_ws_urls

websocket_urlpatterns = [
    re_path("ws/", URLRouter(api_ws_urls)),
]
