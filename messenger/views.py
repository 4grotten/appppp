from django.db.models import Q
from messenger.constants import ADMIN, GROUP, MEMBER
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException
from common.pagination import GeneralPagination
from messenger.models import (
    ChatFolder,
    MessengerChat,
    ChatMember,
    ChatMessage,
    BlockedChat,
)
from messenger.serializers import (
    ChatFolderSerializer,
    ChatMessageWSSerializer,
    ListChatFolderSerializer,
    MessengerChatSerializer,
    ChatMessageSerializer,
    MessengerChatListSerializer,
    MessageLikeSerializer,
    ChatMessageUpdateSerializer,
    MessengerChatUpdateSerializer,
)
from messenger.services import (
    FoldersChatSerivice,
    MessengerChatService,
    ChatMessageService,
)
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


class GetOrCreatePrivateChatView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessengerChatListSerializer

    def get_queryset(self):
        return MessengerChat.objects.filter(members=self.request.user).distinct()

    def post(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response(
                {"detail": "'user_id' is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        if str(request.user.id) == str(user_id):
            return Response(
                {"detail": "You can't create chat with yourself."},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_user = UserService.get(id=user_id)

        existing_chat = (
            MessengerChatService.filter(
                chat_type="private", members__id=request.user.id
            )
            .filter(members__id=target_user.id)
            .distinct()
            .first()
        )

        serializer = MessengerChatSerializer(
            existing_chat, context={"request": request}
        )
        if existing_chat:
            return Response(serializer.data, status=status.HTTP_200_OK)

        chat = MessengerChat.objects.create(chat_type="private")
        ChatMember.objects.bulk_create(
            [
                ChatMember(chat=chat, user=request.user),
                ChatMember(chat=chat, user=target_user),
            ]
        )

        serializer = MessengerChatSerializer(chat, context={"request": request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatMessageListView(ListAPIView, RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = ChatMessageSerializer

    def get_object(self):
        return MessengerChatService.get(id=self.kwargs["pk"])

    def get_queryset(self):
        chat = MessengerChatService.get(id=self.kwargs["pk"])
        return ChatMessage.objects.filter(chat=chat).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        chat = MessengerChatService.get(id=self.kwargs["pk"])
        response = super().list(request, args, kwargs)
        response.data["wallpapers"] = CommentService.get_user_theme_or_default(
            user=self.request.user
        )
        response.data["chat"] = MessengerChatSerializer(
            chat, context={"request": request}
        ).data
        return response

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkMessagesAsReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user = request.user
        chat = MessengerChatService.get(pk=kwargs["pk"])

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

        if hasattr(chat, "blockedchat") and chat.blockedchat.blocked_by != request.user:
            return Response(
                {"detail": "This chat already was blocked by other user"}, status=403
            )

        if hasattr(chat, "blockedchat") and chat.blockedchat.blocked_by == request.user:
            return Response({"detail": "You already blocked this chat"}, status=400)

        BlockedChat.objects.create(chat=chat, blocked_by=request.user)
        return Response({"detail": "Successfully blocked chat."}, status=200)

    def delete(self, request, chat_id):
        chat = MessengerChatService.get(pk=chat_id)

        if not hasattr(chat, "blockedchat"):
            return Response({"detail": "Chat is not blocked"}, status=400)

        if chat.blockedchat.blocked_by != request.user:
            return Response({"detail": "You can't unblock this chat."}, status=403)

        chat.blockedchat.delete()
        return Response({"detail": "Successfully unblocked chat"}, status=200)


class ChatMessageLike(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination

    def create(self, request, *args, **kwargs):
        serializer = MessageLikeSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        message = serializer.validated_data["message"]
        ChatMessageService.like_unlike_message(
            user=request.user,
            message=message,
            is_liked=serializer.validated_data["is_liked"],
        )

        # WebSocket отправка обновления
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.chat.id}",
            {
                "type": "chat_message_update",
                "message": ChatMessageWSSerializer(
                    message, context={"user": request.user}
                ).data,
            },
        )

        return Response(data={"message": _("Successfully updated like status")})


class ChatMessageDestroyUpdateRetrieveView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatMessageSerializer
    queryset = ChatMessage.objects.all()

    def update(self, request, *args, **kwargs):
        message = self.get_object()
        serializer = ChatMessageUpdateSerializer(message, data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        if self.request.user != message.sender:
            raise NotAcceptableException(_("No rights to edit message"))

        serializer.save()

        # WebSocket отправка обновления
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.chat.id}",
            {
                "type": "chat_message_update",
                "message": ChatMessageWSSerializer(
                    message, context={"user": request.user}
                ).data,
            },
        )

        return Response(
            data={"message": _("Successfully updated message")},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, *args, **kwargs):
        message = self.get_object()
        if self.request.user == message.sender:

            ChatMessageService.delete_message(message=message)
            return Response(
                data={
                    "message": _("Successfully deleted message"),
                },
                status=status.HTTP_200_OK,
            )
        raise NotAcceptableException(_("No rights to delete message"))


class FolderListCreateAPIView(ListCreateAPIView):
    queryset = ChatFolder.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ChatFolderSerializer
        return ListChatFolderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.request.user
        instance = FoldersChatSerivice.create(user, serializer.validated_data)
        return Response(
            self.get_serializer(instance).data, status=status.HTTP_201_CREATED
        )


class FolderUpdateAPIView(RetrieveUpdateDestroyAPIView):
    queryset = ChatFolder.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = ChatFolderSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MessengerChatsDeleteAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        chat_ids = request.data.get("chats", [])
        if not isinstance(chat_ids, list):
            return Response(
                {"error": "chats must be a list of IDs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chats = MessengerChat.objects.filter(id__in=chat_ids)
        deleted_count = chats.count()
        chats.delete()
        return Response({"deleted": deleted_count}, status=status.HTTP_200_OK)


class MessengerChatsViewAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        chat_ids = request.data.get("chats", [])
        if not isinstance(chat_ids, list):
            return Response(
                {"error": "chats must be a list of IDs"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chats = MessengerChat.objects.filter(id__in=chat_ids)
        messages = ChatMessage.objects.filter(chat__in=chats).exclude(
            sender=request.user
        )

        messages.update(is_read=True)

        return Response({"updated": len(chats)}, status=status.HTTP_200_OK)


class MessengerChatsBlockAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        chat_ids = request.data.get("chats", [])
        if not isinstance(chat_ids, list):
            return Response({"error": "chats must be a list of IDs"}, status=400)

        user = request.user
        chats = MessengerChat.objects.filter(id__in=chat_ids)

        blocked_chats = BlockedChat.objects.filter(chat__in=chats)
        blocked_map = {b.chat_id: b.blocked_by_id for b in blocked_chats}

        to_create = []
        errors = []

        for chat in chats:
            if chat.id in blocked_map:
                if blocked_map[chat.id] != user.id:
                    errors.append(f"Chat {chat.id} blocked by another user")
                else:
                    errors.append(f"Chat {chat.id} already blocked by you")
            else:
                to_create.append(BlockedChat(chat=chat, blocked_by=user))

        BlockedChat.objects.bulk_create(to_create)

        return Response(
            {
                "blocked_count": len(to_create),
                "errors": errors,
            },
            status=200,
        )


class MessengerChatsUnBlockAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        chat_ids = request.data.get("chats", [])
        if not isinstance(chat_ids, list):
            return Response({"error": "chats must be a list of IDs"}, status=400)

        user = request.user
        results = {"unblocked": [], "errors": []}

        for chat_id in chat_ids:
            try:
                chat = MessengerChatService.get(pk=chat_id)
            except MessengerChat.DoesNotExist:
                results["errors"].append(f"Chat {chat_id} does not exist")
                continue

            if not hasattr(chat, "blockedchat"):
                results["errors"].append(f"Chat {chat_id} is not blocked")
                continue

            if chat.blockedchat.blocked_by != user:
                results["errors"].append(
                    f"You can't unblock chat {chat_id} blocked by another user"
                )
                continue

            chat.blockedchat.delete()
            results["unblocked"].append(chat_id)

        return Response(results, status=200)


class GetOrCreateGroupChatView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessengerChatListSerializer

    def get_queryset(self):
        return MessengerChat.objects.filter(members=self.request.user).distinct()

    def post(self, request):
        users_ids = request.data.get("users_ids")
        title = request.data.get("title")
        image = request.data.get("image")

        if not users_ids or not title:
            return Response(
                {"detail": "'users_ids' and 'title' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if str(request.user.id) in users_ids:
            return Response(
                {"detail": "You can't create chat with yourself."},
                status=status.HTTP_403_FORBIDDEN,
            )

        target_users = UserService.filter(id__in=users_ids)

        chat = MessengerChat.objects.create(chat_type=GROUP, title=title, image=image)

        chat_members = [
            ChatMember(chat=chat, user=request.user, role=ADMIN),
        ]
        for user in target_users:
            chat_members.append(ChatMember(chat=chat, user=user))

        ChatMember.objects.bulk_create(chat_members)

        serializer = MessengerChatSerializer(chat, context={"request": request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UpdateGroupChatAPIView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MessengerChatUpdateSerializer
    queryset = MessengerChat.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddUsersToGroupChatAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        chat = MessengerChatService.get(id=pk)
        if not chat:
            return Response(
                {"detail": "Chat not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if chat.chat_type != "group":
            return Response(
                {"detail": "This endpoint is for group chats only."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users_ids = request.data.get("users_ids", [])
        if not users_ids:
            return Response(
                {"detail": "'users_ids' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if str(request.user.id) not in users_ids:
            return Response(
                {"detail": "You must be a member of the chat to add users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not chat.members.filter(user=request.user, role=ADMIN).exists():
            return Response(
                {"detail": "You must be an admin to add users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        new_members = []
        for user_id in users_ids:
            user = UserService.get(id=user_id)
            if user and user not in chat.members.all():
                new_members.append(ChatMember(chat=chat, user=user))

        ChatMember.objects.bulk_create(new_members)

        serializer = MessengerChatSerializer(chat, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ExitGroupChatAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        chat = MessengerChatService.get(id=pk)
        if not chat:
            return Response(
                {"detail": "Chat not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if chat.chat_type != "group":
            return Response(
                {"detail": "This endpoint is for group chats only."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not chat.members.filter(user=request.user).exists():
            return Response(
                {"detail": "You are not a member of this chat."},
                status=status.HTTP_403_FORBIDDEN,
            )

        chat.members.filter(user=request.user).delete()

        return Response({"detail": "You have exited the group chat."}, status=200)


class DeleteUsersFromGroupChatAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        chat = MessengerChatService.get(id=pk)
        if not chat:
            return Response(
                {"detail": "Chat not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if chat.chat_type != "group":
            return Response(
                {"detail": "This endpoint is for group chats only."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users_ids = request.data.get("users_ids", [])
        if not users_ids:
            return Response(
                {"detail": "'users_ids' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if str(request.user.id) not in users_ids:
            return Response(
                {"detail": "You must be a member of the chat to delete users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if not chat.members.filter(user=request.user, role=ADMIN).exists():
            return Response(
                {"detail": "You must be an admin to delete users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        for user_id in users_ids:
            user = UserService.get(id=user_id)
            if user and user in chat.members.all():
                chat.members.filter(user=user).delete()

        serializer = MessengerChatSerializer(chat, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeGroupChatOwnerAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        chat = MessengerChatService.get(id=pk)
        if not chat:
            return Response(
                {"detail": "Chat not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if chat.chat_type != "group":
            return Response(
                {"detail": "This endpoint is for group chats only."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user_id = request.data.get("user_id")
        role = request.data.get("role", None)
        if not user_id or not role:
            return Response(
                {"detail": "'user_id' and ''role' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = UserService.get(id=user_id)
        if not user or user not in chat.members.all():
            return Response(
                {"detail": "User must be in of the chat."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not chat.members.filter(user=request.user, role=ADMIN).exists():
            return Response(
                {"detail": "You must be an admin to change the owner."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if role not in [ADMIN, MEMBER]:
            return Response(
                {"detail": "Role must be 'admin' or 'member'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        chat.members.filter(user=user).update(role=role)

        serializer = MessengerChatSerializer(chat, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
