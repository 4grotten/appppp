from django.db.models import Q
from django.shortcuts import render
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import GeneralPagination
from messenger.models import MessengerChat, ChatMember, ChatMessage, BlockedChat
from messenger.serializers import MessengerChatSerializer, ChatMessageSerializer, ChatMessageCreateSerializer
from messenger.services import MessengerChatService, ChatMessageService
from shop.services.comment_services import CommentService
from users.models import User
from users.serializers import UserShortInfoSerializer
from users.services import UserService


class FindUserView(APIView):
    def get(self, request):
        query = request.query_params.get("query")

        if not query:
            return Response(
                {"detail": "Set 'query' (id or phone_number)"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = None

        # Пробуем как ID (число)
        if query.isdigit():
            user = UserService.filter(id=int(query)).first()

        # Если не нашли по ID — пробуем как телефон
        if not user:
            phone_number = "+" + query.strip()
            user = UserService.get(phone_number=phone_number)

        serializer = UserShortInfoSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetOrCreatePrivateChatView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"detail": "'user_id' is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if str(request.user.id) == str(user_id):
            return Response({"detail": "You can't create chat with yourself."},
                            status=status.HTTP_400_BAD_REQUEST)

        target_user = UserService.get(id=user_id)

        existing_chat = MessengerChatService.filter(
            chat_type="private",
            members__id=request.user.id
        ).filter(
            members__id=target_user.id
        ).distinct().first()

        serializer = MessengerChatSerializer(existing_chat, context={"request": request})
        if existing_chat:
            return Response(serializer.data, status=status.HTTP_200_OK)

        chat = MessengerChat.objects.create(chat_type="private")
        ChatMember.objects.bulk_create([
            ChatMember(chat=chat, user=request.user),
            ChatMember(chat=chat, user=target_user),
        ])

        serializer = MessengerChatSerializer(chat, context={"request": request})

        return Response({
            serializer.data
        }, status=status.HTTP_201_CREATED)


class ChatMessageListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        chat = MessengerChatService.get(id=self.kwargs['pk'])
        return ChatMessage.objects.filter(chat=chat).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        chat = MessengerChatService.get(id=self.kwargs['pk'])
        response = super().list(request, args, kwargs)
        response.data['wallpapers'] = CommentService.get_user_theme_or_default(user=self.request.user)
        response.data['chat'] = MessengerChatSerializer(chat, context={'request': request}).data
        return response


class MarkMessagesAsReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        chat = MessengerChatService.get(pk=kwargs['pk'])

        updated_count = ChatMessage.objects.filter(
            ~Q(sender=user),
            chat=chat,
            is_read=False,
        ).update(is_read=True, is_delivered=True)

        return Response({"detail": f"{updated_count} messages marked as read."})


class ChatBlockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = MessengerChatService.get(pk=chat_id)

        if hasattr(chat, 'blockedchat') and chat.blockedchat.blocked_by != request.user:
            return Response({"detail": "This chat already was blocked by other user"}, status=403)

        if hasattr(chat, 'blockedchat') and chat.blockedchat.blocked_by == request.user:
            return Response({"detail": "You already blocked this chat"}, status=200)

        BlockedChat.objects.create(chat=chat, blocked_by=request.user)
        return Response({"detail": "Successfully blocked chat."}, status=200)

    def delete(self, request, chat_id):
        chat = MessengerChatService.get(pk=chat_id)

        if not hasattr(chat, 'blockedchat'):
            return Response({"detail": "Chat is not blocked"}, status=400)

        if chat.blockedchat.blocked_by != request.user:
            return Response({"detail": "You can't unblock this chat."}, status=403)

        chat.blockedchat.delete()
        return Response({"detail": "Successfully unblocked chat"}, status=200)
