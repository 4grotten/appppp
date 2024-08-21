from django.urls import re_path
from organizations.consumers import CommentConsumer

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<chat_id>\d+)/$', CommentConsumer.as_asgi())
]
