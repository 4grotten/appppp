from django.urls import path, include

from messenger.views import (
    ChatMessageDestroyUpdateRetrieveView,
    ChatMessageLike,
    FindUserView,
    ForwardMessageAPIView,
    GetOrCreatePrivateChatView,
    ReplyMessageAPIView,
)

messages_url = [
    path("messenger/users/", FindUserView.as_view(), name="users-find"),
    path("messenger/chats/", GetOrCreatePrivateChatView.as_view(), name="chats"),
    path("messenger/likes/", ChatMessageLike.as_view(), name="messages-likes"),
    path(
        "messenger/messages/<int:pk>/",
        ChatMessageDestroyUpdateRetrieveView.as_view(),
        name="messages-update-destroy",
    ),
    path(
        "messenger/forward-message/",
        ForwardMessageAPIView.as_view(),
        name="messages-forward",
    ),
    path(
        "nessenger/reply-message/",
        ReplyMessageAPIView.as_view(),
        name="messages-reply",
    ),
]
