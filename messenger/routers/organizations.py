from django.urls import path, include

from messenger.views import (
    MessengerChatsOrganiationAPIView,
)

organization_urls = [
    path(
        "messenger/chats/organization/",
        MessengerChatsOrganiationAPIView.as_view(),
        name="messenger-chats-organization",
    )
]
