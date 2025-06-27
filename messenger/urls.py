from django.urls import path, include

from messenger.views import FindUserView, GetOrCreatePrivateChatView, ChatMessageListView, MarkMessagesAsReadView, \
    ChatBlockView

messenger_urls = [
    path("messenger/users/", FindUserView.as_view(), name="users-find"),
    path("messenger/chats/", GetOrCreatePrivateChatView.as_view(), name="chats"),
    path("messenger/chats/<int:pk>/", ChatMessageListView.as_view(), name="chat-messages-list"),
    path("messenger/chats/<int:pk>/mark-as-read/", MarkMessagesAsReadView.as_view(), name='chat_mark_read'),
    path("messenger/chats/<int:chat_id>/block/", ChatBlockView.as_view(), name='chat-block'),
]

urlpatterns = [
    path('', include(messenger_urls)),
]

