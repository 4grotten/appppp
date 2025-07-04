from django.urls import path, include

from messenger.routers import private_chats, messages, folders
from messenger.views import (
    MessengerChatsBlockAPIView,
    MessengerChatsDeleteAPIView,
    MessengerChatsUnBlockAPIView,
    MessengerChatsViewAPIView,
)

messenger_urls = [
    path(
        "messenger/chats/delete/",
        MessengerChatsDeleteAPIView.as_view(),
        name="chats-delete",
    ),
    path(
        "messenger/chats/view/",
        MessengerChatsViewAPIView.as_view(),
        name="chats-view",
    ),
    path(
        "messenger/chats/block/",
        MessengerChatsBlockAPIView.as_view(),
        name="chats-block",
    ),
    path(
        "messenger/chats/unblock/",
        MessengerChatsUnBlockAPIView.as_view(),
        name="chats-unblock",
    ),
]


urlpatterns = [
    path("", include(messenger_urls)),
    path("", include(private_chats.private_chats_url)),
    path("", include(messages.messages_url)),
    path("", include(folders.folders_url)),
]
