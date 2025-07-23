from django.urls import path, include

from messenger.views import (
    MessengerChatsOrganiationAPIView,
    MessengerChatsOrganizationDetailAPIView,
)

organization_urls = [
    path(
        "messenger/chats/organization/",
        MessengerChatsOrganiationAPIView.as_view(),
        name="messenger-chats-organization",
    ),
    path(
        "messenger/chats/organization/<int:organization_id>/",
        MessengerChatsOrganizationDetailAPIView.as_view(),
        name="messenger-chats-organization-detail",
    ),
]
