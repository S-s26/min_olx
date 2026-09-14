"""
WebSocket URL patterns for the chat app.

URLs are namespaced so the chat consumer can resolve the chatroom id
and enforce that the connected user is one of the participants.
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/chat/(?P<room_id>\d+)/$',
        consumers.ChatConsumer.as_asgi(),
    ),
]