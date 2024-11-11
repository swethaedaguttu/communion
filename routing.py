# routing.py
from django.urls import path
from . import consumers  # Import your consumer

websocket_urlpatterns = [
    path('ws/interfaith/', consumers.ChatConsumer.as_asgi()),  # Define a URL for WebSocket connections
    re_path(r'ws/notifications/', consumers.NotificationConsumer.as_asgi()),  # WebSocket endpoint

    
]
