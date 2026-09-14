"""
ASGI config for mini_olx project.

Routes HTTP through Django's standard handler and WebSocket traffic
through Channels (chat consumers). Designed to be served by daphne
(or uvicorn) in production and run with `python manage.py runserver`
in development.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mini_olx.settings')

# Initialise Django ASGI application early so apps are loaded before
# import of any consumer/routing modules that touch the ORM.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from chat.routing import websocket_urlpatterns


application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})