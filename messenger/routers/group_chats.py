from django.urls import path, include
from messenger.views import GetOrCreateGroupChatView, UpdateGroupChatAPIView

group_chats_url = [
    path(
        "messenger/group/",
        GetOrCreateGroupChatView.as_view(),
        name="messenger-group-create",
    ),
    path(
        "messenger/group/<int:pk>/",
        UpdateGroupChatAPIView.as_view(),
        name="messenger-group-update",
    ),
]
