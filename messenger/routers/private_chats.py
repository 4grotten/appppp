from django.urls import path, include

from messenger.views import (
    ChatMessageListView,
    MarkMessagesAsReadView,
    ChatBlockView,
)

private_chats_url = [
    path(
        "messenger/chats/<int:pk>/",
        ChatMessageListView.as_view(),
        name="chat-messages-list",
    ),
    path(
        "messenger/chats/<int:pk>/mark-as-read/",
        MarkMessagesAsReadView.as_view(),
        name="chat_mark_read",
    ),
    path(
        "messenger/chats/<int:chat_id>/block/",
        ChatBlockView.as_view(),
        name="chat-block",
    ),
]
