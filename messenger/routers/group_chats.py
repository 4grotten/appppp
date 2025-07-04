from django.urls import path, include
from messenger.views import GetOrCreateGroupChatView

group_chats_url = [
    path(
        "messenger/group/",
        GetOrCreateGroupChatView.as_view(),
        name="messenger-group-create",
    )
]
