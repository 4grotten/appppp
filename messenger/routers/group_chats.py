from django.urls import path
from messenger.views import (
    AddUsersToGroupChatAPIView,
    ChangeGroupChatOwnerAPIView,
    DeleteUsersFromGroupChatAPIView,
    ExitGroupChatAPIView,
    GetOrCreateGroupChatView,
    UpdateGroupChatAPIView,
)

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
    path(
        "messenger/group/<int:pk>/add-users/",
        AddUsersToGroupChatAPIView.as_view(),
        name="messenger-group-add-users",
    ),
    path(
        "messenger/group/<int:pk>/exit/",
        ExitGroupChatAPIView.as_view(),
        name="messenger-group-exit",
    ),
    path(
        "messenger/group/<>int:pk>/delete-users/",
        DeleteUsersFromGroupChatAPIView.as_view(),
        name="messenger-group-delete-users",
    ),
    path(
        "messenger/group/<int:pk>/change-role/",
        ChangeGroupChatOwnerAPIView.as_view(),
        name="messenger-group-change-owner",
    ),
]
