"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/asgi/
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

import django
django.setup()
from django.urls import re_path

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

from messenger.consumers import ChatConsumer
from organizations.consumers import CommentConsumer, CommentItemConsumer
from organizations.middleware import TokenAuthMiddleware



application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": TokenAuthMiddleware(
        URLRouter([
            re_path(r'ws/chat/(?P<chat_id>\d+)/$', CommentConsumer.as_asgi()),
            re_path(r'ws/assistant-response/(?P<chat_id>\d+)/$', CommentItemConsumer.as_asgi()),
            re_path(r'ws/messenger/chat/(?P<chat_id>\d+)/$', ChatConsumer.as_asgi()),
        ])
    ),
})


