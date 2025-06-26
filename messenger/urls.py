from django.urls import path, include

from messenger.views import FindUserView, GetOrCreatePrivateChatView, ChatMessageListView

messenger_urls = [
    path("messenger/users/", FindUserView.as_view(), name="users-find"),
    path("messenger/chats/", GetOrCreatePrivateChatView.as_view(), name="chats"),
    path("messenger/chats/<int:pk>/", ChatMessageListView.as_view(), name="chat-messages-list"),
]

urlpatterns = [
    path('', include(messenger_urls)),
]

