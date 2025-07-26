import logging

from django.db.models import Q, Exists, OuterRef, Subquery, IntegerField, Value, Count
from django.shortcuts import get_object_or_404
from django.db.models.functions import Coalesce

from messenger.constants import (
    ADMIN,
    GROUP,
    MEMBER,
    PRIVATE,
)
from messenger.utils import (
    get_chat_translation,
    send_push_message_chat,
    send_unread_message_count_via_ws,
)
from organizations.models import Organization
from rest_framework import status
from rest_framework.generics import (
    ListCreateAPIView,
    ListAPIView,
    CreateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync, sync_to_async

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
    OrganizationChatDetailSerializer,
    OrganizationSimpleSerializer,
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
    services_class = MessengerChatService

    def get_queryset(self):
        sort_by = self.request.query_params.get("sort_by")
        organization_id = self.request.query_params.get("organization_id")
        queryset = MessengerChat.objects.filter(members=self.request.user).distinct()
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        else:
            queryset = queryset.filter(organization__isnull=True)
        unread_count_subquery = (
            ChatMessage.objects.filter(
                chat=OuterRef("pk"), is_read=False, sender__is_active=True
            )
            .exclude(sender=self.request.user)
            .values("chat")
            .annotate(count=Count("id"))
            .values("count")
        )

        queryset = queryset.annotate(
            unread_messages_count=Coalesce(
                Subquery(unread_count_subquery, output_field=IntegerField()), Value(0)
            )
        )
        if sort_by:
            queryset = self.services_class.sort_by(
                queryset, sort_by, user=self.request.user
            )
        return queryset

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
        chat = sync_to_async(MessengerChatService.get, thread_sensitive=True)(
            id=self.kwargs["pk"]
        ).result()

        response = super().list(request, *args, **kwargs)

        wallpapers = sync_to_async(
            CommentService.get_user_theme_or_default, thread_sensitive=True
        )(user=self.request.user).result()

        response.data["wallpapers"] = wallpapers
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
        send_unread_message_count_via_ws(user)
        return Response({"detail": f"{updated_count} messages marked as read."})


class ChatBlockView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, chat_id):
        chat = MessengerChatService.get(pk=chat_id)
        user = request.user
        if hasattr(chat, "blockedchat") and chat.blockedchat.blocked_by != user:
            return Response(
                {"detail": "This chat already was blocked by other user"}, status=403
            )

        if hasattr(chat, "blockedchat") and chat.blockedchat.blocked_by == user:
            return Response({"detail": "You already blocked this chat"}, status=400)
        language = request.headers.get("Accept-Language", "en").lower()[:2]
        participants = (
            ChatMember.objects.filter(chat=chat)
            .exclude(user=user)
            .select_related("user")
        )

        for member in participants:
            is_group = chat.chat_type != "private"
            message_body = get_chat_translation("blocked", language, is_group=is_group)
            message_title = chat.title if is_group else f"{user.full_name}"

            send_push_message_chat(
                user=member.user,
                title=message_title,
                body=(f"{user.full_name} {message_body}" if is_group else message_body),
                chat_id=chat.id,
                is_group=is_group,
            )
        BlockedChat.objects.create(chat=chat, blocked_by=request.user)
        return Response({"detail": "Successfully blocked chat."}, status=200)

    def delete(self, request, chat_id):
        chat = MessengerChatService.get(pk=chat_id)
        user = request.user
        language = request.headers.get("Accept-Language", "en").lower()[:2]
        if not hasattr(chat, "blockedchat"):
            return Response({"detail": "Chat is not blocked"}, status=400)

        if chat.blockedchat.blocked_by != user:
            return Response({"detail": "You can't unblock this chat."}, status=403)
        participants = (
            ChatMember.objects.filter(chat=chat)
            .exclude(user=user)
            .select_related("user")
        )

        for member in participants:
            is_group = chat.chat_type != "private"
            message_body = get_chat_translation(
                "unblocked", language, is_group=is_group
            )
            message_title = chat.title if is_group else f"{user.full_name}"

            send_push_message_chat(
                user=member.user,
                title=message_title,
                body=(f"{user.full_name} {message_body}" if is_group else message_body),
                chat_id=chat.id,
                is_group=is_group,
            )
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
        language = request.headers.get("Accept-Language", "en").lower()[:2]

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
                continue
            participants = (
                ChatMember.objects.filter(chat=chat)
                .exclude(user=user)
                .select_related("user")
            )

            for member in participants:
                is_group = chat.chat_type != "private"
                message_body = get_chat_translation(
                    "blocked", language, is_group=is_group
                )
                message_title = chat.title if is_group else f"{user.full_name}"

                send_push_message_chat(
                    user=member.user,
                    title=message_title,
                    body=(
                        f"{user.full_name} {message_body}" if is_group else message_body
                    ),
                    chat_id=chat.id,
                    is_group=is_group,
                )
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
    services_class = MessengerChatService

    def get_queryset(self):
        sort_by = self.request.query_params.get("sort_by")
        organization_id = self.request.query_params.get("organization_id")
        queryset = MessengerChat.objects.filter(members=self.request.user).distinct()
        if organization_id:
            queryset = queryset.filter(organization_id=organization_id)
        else:
            queryset = queryset.filter(organization__isnull=True)
        unread_count_subquery = (
            ChatMessage.objects.filter(
                chat=OuterRef("pk"), is_read=False, sender__is_active=True
            )
            .exclude(sender=self.request.user)
            .values("chat")
            .annotate(count=Count("id"))
            .values("count")
        )

        queryset = queryset.annotate(
            unread_messages_count=Coalesce(
                Subquery(unread_count_subquery, output_field=IntegerField()), Value(0)
            )
        )
        if sort_by:
            queryset = self.services_class.sort_by(
                queryset, sort_by, user=self.request.user
            )
        return queryset

    def post(self, request):
        users_ids = request.data.getlist("users_ids")
        title = request.data.get("title")
        image = request.data.get("image")

        if not title:
            return Response(
                {"detail": "'title' is required."},
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


class UpdateGroupChatAPIView(ListAPIView, RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    pagination_class = GeneralPagination
    serializer_class = ChatMessageSerializer

    def get_object(self):
        return MessengerChatService.get(id=self.kwargs["pk"])

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return MessengerChatUpdateSerializer
        return super().get_serializer_class()

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
        language = request.headers.get("Accept-Language", "en").lower()[:2]
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
        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response(
                {"detail": "You must be a member of the chat to add users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not ChatMember.objects.filter(
            chat=chat, user=request.user, role=ADMIN
        ).exists():
            return Response(
                {"detail": "You must be an admin to add users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        new_members = []
        for user_id in users_ids:
            user = UserService.get(id=user_id)
            if user and user not in chat.members.all():
                new_members.append(ChatMember(chat=chat, user=user))

        new_members = ChatMember.objects.bulk_create(new_members)
        for member in new_members:
            is_group = True
            message_body = get_chat_translation(
                "added_member", language, is_group=is_group
            )
            message_title = chat.title if is_group else f"{request.user.full_name}"

            send_push_message_chat(
                user=member.user,
                title=message_title,
                body=(
                    f"{request.user.full_name} {message_body}"
                    if is_group
                    else message_body
                ),
                chat_id=chat.id,
                is_group=is_group,
            )
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

        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response(
                {"detail": "You are not a member of this chat."},
                status=status.HTTP_403_FORBIDDEN,
            )

        ChatMember.objects.filter(chat=chat, user=request.user).delete()

        return Response({"detail": "You have exited the group chat."}, status=200)


class DeleteUsersFromGroupChatAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        language = request.headers.get("Accept-Language", "en").lower()[:2]
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
        if not ChatMember.objects.filter(chat=chat, user=request.user).exists():
            return Response(
                {"detail": "You must be a member of the chat to add users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not ChatMember.objects.filter(
            chat=chat, user=request.user, role=ADMIN
        ).exists():
            return Response(
                {"detail": "You must be an admin to add users."},
                status=status.HTTP_403_FORBIDDEN,
            )

        participants = (
            ChatMember.objects.filter(chat=chat)
            .exclude(user=request.user)
            .select_related("user")
        )

        for member in participants:
            is_group = chat.chat_type != "private"
            message_body = get_chat_translation(
                "deleted_member", language, is_group=is_group
            )
            message_title = chat.title if is_group else f"{request.user.full_name}"

            send_push_message_chat(
                user=member.user,
                title=message_title,
                body=(
                    f"{request.user.full_name} {message_body}"
                    if is_group
                    else message_body
                ),
                chat_id=chat.id,
                is_group=is_group,
            )
        for user_id in users_ids:
            user = UserService.get(id=user_id)
            if user and chat.members.filter(id=user.id).exists():
                ChatMember.objects.filter(chat=chat, user=user).delete()
        serializer = MessengerChatSerializer(chat, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChangeGroupChatOwnerAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):

        language = request.headers.get("Accept-Language", "en").lower()[:2]
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

        if not ChatMember.objects.filter(
            chat=chat, user=request.user, role=ADMIN
        ).exists():
            return Response(
                {"detail": "You must be an admin to add users."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if role not in [ADMIN, MEMBER]:
            return Response(
                {"detail": "Role must be 'admin' or 'member'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        ChatMember.objects.filter(user=user, chat=chat).update(role=role)
        member = ChatMember.objects.get(user=user, chat=chat)
        is_group = True
        admin_member = "appointed_admin" if role == ADMIN else "removed_admin"
        message_body = get_chat_translation(admin_member, language, is_group=is_group)
        message_title = chat.title if is_group else f"{request.user.full_name}"

        send_push_message_chat(
            user=member.user,
            title=message_title,
            body=(
                f"{request.user.full_name} {message_body}" if is_group else message_body
            ),
            chat_id=chat.id,
            is_group=is_group,
        )

        serializer = MessengerChatSerializer(chat, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ForwardMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Ожидает в body JSON:
        {
            "original_message_id": int,  # id сообщения, которое пересылаем
            "target_chat_ids": list[int]         # id чата, куда пересылаем
        }
        """
        original_message_id = request.data.get("original_message_id")
        target_chat_ids = request.data.get("target_chat_ids")

        if not original_message_id or not target_chat_ids:
            return Response(
                {"detail": "original_message_id и target_chat_id обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        original_message = get_object_or_404(ChatMessage, id=original_message_id)
        for target_chat_id in target_chat_ids:
            target_chat = get_object_or_404(MessengerChat, id=target_chat_id)
            forwarded_message = ChatMessage.objects.create(
                chat=target_chat,
                sender=request.user,
                text="",
                forwarded_from=original_message.sender,
                parent=original_message.parent,
                forwarded_message=original_message,
            )
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"chat_{forwarded_message.chat.id}",
                {
                    "type": "chat_message",
                    "message": ChatMessageWSSerializer(
                        forwarded_message, context={"user": request.user}
                    ).data,
                },
            )
            participant_ids = list(
                forwarded_message.chat.members.values_list("id", flat=True)
            )
            for user_id in participant_ids:
                user = User.objects.get(id=user_id)
                serializer = ChatMessageWSSerializer(
                    forwarded_message, context={"user": user}
                )
                response_json = serializer.data
                async_to_sync(channel_layer.group_send)(
                    f"user_{user_id}_chats",
                    {
                        "type": "chat_list_update",
                        "chat_id": forwarded_message.chat.id,
                        "last_message": response_json,
                    },
                )

        data = {
            "detail": "Successfully forwarded message",
        }

        return Response(data, status=status.HTTP_201_CREATED)


class ReplyMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Ожидает в body JSON:
        {
            "chat_id": int,         # id чата, где создаётся ответ
            "parent_message_id": int,  # id сообщения, на которое отвечают
            "text": str             # текст ответа
        }
        """
        chat_id = request.data.get("chat_id")
        parent_message_id = request.data.get("parent_message_id")
        text = request.data.get("text")

        if not chat_id or not parent_message_id or not text:
            return Response(
                {"detail": "chat_id, parent_message_id и text обязательны"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        chat = get_object_or_404(MessengerChat, id=chat_id)
        parent_message = get_object_or_404(ChatMessage, id=parent_message_id)

        if parent_message.chat_id != chat.id:
            return Response(
                {
                    "detail": "Сообщение, на которое отвечают, должно принадлежать тому же чату"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reply_message = ChatMessage.objects.create(
            chat=chat,
            sender=request.user,
            text=text,
            parent=parent_message,
        )
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{reply_message.chat.id}",
            {
                "type": "chat_message",
                "message": ChatMessageWSSerializer(
                    reply_message, context={"user": request.user}
                ).data,
            },
        )
        participant_ids = list(reply_message.chat.members.values_list("id", flat=True))
        for user_id in participant_ids:
            user = User.objects.get(id=user_id)
            serializer = ChatMessageWSSerializer(reply_message, context={"user": user})
            response_json = serializer.data
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}_chats",
                {
                    "type": "chat_list_update",
                    "chat_id": reply_message.chat.id,
                    "last_message": response_json,
                },
            )
        data = {
            "detail": "Successfully created reply message",
        }

        return Response(data, status=status.HTTP_201_CREATED)


class MessengerChatsUnReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        unread_message_count = (
            ChatMessage.objects.filter(
                chat__members=user,
                is_read=False,
            )
            .exclude(sender=user)
            .count()
        )

        return Response(
            {"unread_chat_count": unread_message_count}, status=status.HTTP_200_OK
        )


class MessengerChatsOrganiationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        user_chats_subquery = MessengerChat.objects.filter(
            organization=OuterRef("pk"),
            chatmember__user=user,
        )

        organizations = Organization.objects.annotate(
            user_in_chat=Exists(user_chats_subquery)
        ).filter(user_in_chat=True)

        unread_messages_subquery = ChatMessage.objects.filter(
            chat__organization=OuterRef("pk"), is_read=False
        ).exclude(sender=user)

        organizations = organizations.annotate(
            unread_messages_count=Coalesce(
                Subquery(
                    unread_messages_subquery.values("chat__organization")
                    .annotate(cnt=Count("id"))
                    .values("cnt"),
                    output_field=IntegerField(),
                ),
                0,
            )
        )

        serializer = OrganizationSimpleSerializer(
            organizations, many=True, context={"request": request}
        )
        return Response(serializer.data, status=200)

    def post(self, request):
        user = request.user
        org_id = request.data.get("organization_id")
        organization = get_object_or_404(Organization, id=org_id)
        users_organization = organization.memberships.filter(
            role__can_send_message=True
        )

        if users_organization.filter(user=user).exists():
            return Response(
                {"detail": "You already have access to this organization."},
                status=200,
            )

        exists_chat = MessengerChat.objects.filter(
            organization=organization,
            chat_type=GROUP,
        )

        if exists_chat:
            if exists_chat.filter(members=user).exists():
                return Response(
                    {
                        "chat_id": exists_chat.first().id,
                        "detail": "You already have access to this organization's group chat.",
                    },
                    status=200,
                )
        chat = MessengerChat.objects.create(
            chat_type=GROUP, title=None, organization=organization
        )
        chat_members = [ChatMember(chat=chat, user=user)]
        for member in users_organization:
            chat_members.append(ChatMember(chat=chat, user=member.user))
        ChatMember.objects.bulk_create(chat_members)

        return Response(
            {"chat_id": chat.id, "detail": "Чат успешно создан."},
            status=status.HTTP_201_CREATED,
        )


class MessengerChatsOrganizationDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organization_id):
        organization = get_object_or_404(Organization, id=organization_id)
        serializer = OrganizationChatDetailSerializer(
            organization, context={"request": request}
        )
        return Response(serializer.data, status=200)
