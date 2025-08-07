from datetime import timedelta
from django.db.models import Count, OuterRef, Subquery, IntegerField, Value
from django.db.models.functions import Coalesce
from common.serializers import ImageSerializer
from instagrapi.types import UserShort
from organizations.models import Organization
from organizations.serializers.categories_serializers import OrganizationTypeSerializer
from organizations.serializers.organization_serializers import OrganizationSerializer
from rest_framework import serializers

from messenger.models import (
    ChatFolder,
    ChatMember,
    MessengerChat,
    ChatMessage,
    MessageLike,
)
from messenger.services import MessengerChatService
from shop.services.comment_services import CommentService
from users.serializers import UserShortInfoSerializer


class OrganizationFinderSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    chat_id = serializers.SerializerMethodField()
    is_members = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    blocked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "title",
            "image",
            "types",
            "chat_id",
            "is_members",
            "updated_at",
            "created_at",
            "blocked_by_me",
            "is_blocked",
        )

    def get_is_blocked(self, organization: Organization):
        request = self.context.get("request")
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.is_blocked()

    def get_blocked_by_me(self, organization: Organization):
        request = self.context.get("request")
        user = request.user
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.is_blocked_by(user)

    def get_updated_at(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.updated_at if chat else None

    def get_created_at(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.created_at if chat else None

    def get_chat_id(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.id if chat else None

    def get_is_members(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return organization.memberships.filter(
            user=request.user, role__can_send_message=True
        ).exists()


class MessengerChatSerializer(serializers.ModelSerializer):
    is_blocked = serializers.SerializerMethodField()
    blocked_by_me = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = MessengerChat
        fields = (
            "id",
            "chat_type",
            "title",
            "members",
            "image",
            "is_blocked",
            "blocked_by_me",
        )

    def get_is_blocked(self, chat):
        return chat.is_blocked()

    def get_blocked_by_me(self, chat):
        request = self.context.get("request")
        return chat.is_blocked_by(request.user) if request else False

    def get_members(self, chat):
        users = chat.members.all()
        serializer = UserShortInfoSerializer(
            users, many=True, context={**self.context, "chat": chat}
        )
        return serializer.data


class ParentChatMessageSerializer(serializers.ModelSerializer):
    user = UserShortInfoSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ("id", "user", "text")


class ChatMessageSerializer(serializers.ModelSerializer):
    is_message_liked = serializers.SerializerMethodField()
    sender = UserShortInfoSerializer(read_only=True)
    message_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = ParentChatMessageSerializer()
    is_updated = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    forwarded = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "sender",
            "parent",
            "text",
            "is_message_liked",
            "message_like_count",
            "can_delete",
            "is_updated",
            "status",
            "created_at",
            "updated_at",
            "forwarded",
            "unread_messages_count",
        )

    def get_is_updated(self, message: ChatMessage) -> bool:
        return (message.updated_at - message.created_at) > timedelta(seconds=1)

    def get_can_delete(self, message: ChatMessage) -> bool:
        user = self.context["request"].user
        return user == message.sender

    def get_is_message_liked(self, message: ChatMessage) -> bool:
        user = self.context["request"].user
        if not user.is_authenticated:
            return False
        return MessengerChatService.is_message_liked_by_user(message=message, user=user)

    def get_message_like_count(self, message: ChatMessage) -> int:
        return message.likes.count()

    def get_status(self, message: ChatMessage) -> str:
        if message.is_read:
            return "read"
        elif message.is_delivered:
            return "delivered"
        elif message.is_sent:
            return "sent"
        return "pending"

    def get_unread_messages_count(self, message: ChatMessage) -> int:
        user = self.context.get("user")
        if not user or not user.is_authenticated:
            return 0
        return (
            ChatMessage.objects.filter(chat=message.chat, is_read=False)
            .exclude(sender=user)
            .count()
        )

    def get_forwarded(self, message: ChatMessage):
        if not message.forwarded_from or not message.forwarded_message:
            return None

        original_sender = message.forwarded_from
        if original_sender:
            full_name = (
                original_sender.get_full_name().strip()
                if callable(getattr(original_sender, "get_full_name", None))
                else ""
            )
            if not full_name or full_name.lower() == "none none":
                full_name = original_sender.username
        else:
            full_name = ""
        return {
            "original_sender": (
                {
                    "id": original_sender.id,
                    "username": original_sender.username,
                    "full_name": full_name,
                }
                if original_sender
                else None
            ),
            "original_message_id": (
                message.forwarded_message.id if message.forwarded_message else None
            ),
            "text": (
                message.forwarded_message.text
                if message.forwarded_message
                else message.text
            ),
        }


class ChatMessageWSSerializer(serializers.ModelSerializer):
    is_message_liked = serializers.SerializerMethodField()
    sender = UserShortInfoSerializer(read_only=True)
    message_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = ParentChatMessageSerializer()
    is_updated = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    forwarded = serializers.SerializerMethodField()
    unread_messages_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = (
            "id",
            "sender",
            "parent",
            "text",
            "is_message_liked",
            "message_like_count",
            "can_delete",
            "is_mine",
            "is_updated",
            "status",
            "created_at",
            "updated_at",
            "forwarded",
            "unread_messages_count",
        )

    def get_is_mine(self, message: ChatMessage):
        user = self.context.get("user")
        return user == message.sender

    def get_is_updated(self, message: ChatMessage) -> bool:
        return (message.updated_at - message.created_at) > timedelta(seconds=1)

    def get_can_delete(self, message: ChatMessage) -> bool:
        user = self.context.get("user")
        return user == message.sender

    def get_is_message_liked(self, message: ChatMessage) -> bool:
        user = self.context.get("user")
        if not user.is_authenticated:
            return False
        return MessengerChatService.is_message_liked_by_user(message=message, user=user)

    def get_message_like_count(self, message: ChatMessage) -> int:
        return message.likes.count()

    def get_status(self, message: ChatMessage) -> str:
        if message.sender == self.context.get("user"):
            if message.is_read:
                return "read"
            elif message.is_delivered:
                return "delivered"
            elif message.is_sent:
                return "sent"
            return "pending"
        else:
            return "read"

    def get_unread_messages_count(self, message: ChatMessage) -> int:
        user = self.context.get("user")
        if not user or not user.is_authenticated:
            return 0
        return (
            ChatMessage.objects.filter(chat=message.chat, is_read=False)
            .exclude(sender=user)
            .count()
        )

    def get_forwarded(self, message: ChatMessage):
        if not message.forwarded_from or not message.forwarded_message:
            return None

        original_sender = message.forwarded_from
        if original_sender:
            full_name = (
                original_sender.get_full_name().strip()
                if callable(getattr(original_sender, "get_full_name", None))
                else ""
            )
            if not full_name or full_name.lower() == "none none":
                full_name = original_sender.username
        else:
            full_name = ""
        return {
            "original_sender": (
                {
                    "id": original_sender.id,
                    "username": original_sender.username,
                    "full_name": full_name,
                }
                if original_sender
                else None
            ),
            "original_message_id": (
                message.forwarded_message.id if message.forwarded_message else None
            ),
            "text": (
                message.forwarded_message.text
                if message.forwarded_message
                else message.text
            ),
        }


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ("parent", "text")

    def validate(self, attrs):
        user = self.context.get("user")
        if not user or not user.is_authenticated:
            raise serializers.ValidationError("User is not authenticated")
        attrs["user"] = user
        return attrs


class LastMessageSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()
    forwarded = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ("id", "text", "created_at", "status", "is_mine", "forwarded")

    def get_status(self, obj: ChatMessage):
        if obj.is_read:
            return "read"
        elif obj.is_delivered:
            return "delivered"
        elif obj.is_sent:
            return "sent"
        return "pending"

    def get_is_mine(self, obj: ChatMessage):
        request = self.context.get("request")
        return obj.sender == request.user if request else False

    def get_forwarded(self, message: ChatMessage):
        if not message.forwarded_from or not message.forwarded_message:
            return None

        original_sender = message.forwarded_from
        if original_sender:
            full_name = (
                original_sender.get_full_name().strip()
                if callable(getattr(original_sender, "get_full_name", None))
                else ""
            )
            if not full_name or full_name.lower() == "none none":
                full_name = original_sender.username
        else:
            full_name = ""
        return {
            "original_sender": (
                {
                    "id": original_sender.id,
                    "username": original_sender.username,
                    "full_name": full_name,
                }
                if original_sender
                else None
            ),
            "original_message_id": (
                message.forwarded_message.id if message.forwarded_message else None
            ),
            "text": (
                message.forwarded_message.text
                if message.forwarded_message
                else message.text
            ),
        }


class MessengerChatListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    blocked_by_me = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()
    unread_messages_count = serializers.IntegerField()
    organization = serializers.SerializerMethodField()

    class Meta:
        model = MessengerChat
        fields = (
            "id",
            "sender",
            "chat_type",
            "title",
            "image",
            "last_message",
            "is_blocked",
            "blocked_by_me",
            "unread_messages_count",
            "organization",
            "created_at",
            "updated_at",
        )

    def get_last_message(self, chat):
        message = chat.messages.order_by("-created_at").first()
        if message:
            return LastMessageSerializer(message, context=self.context).data
        return None

    def get_is_blocked(self, chat):
        return chat.is_blocked()

    def get_blocked_by_me(self, chat):
        user = self.context["request"].user
        return chat.is_blocked_by(user)

    def get_sender(self, chat):
        request_user = self.context["request"].user

        if chat.organization is not None:
            chat_member = (
                ChatMember.objects.filter(chat=chat, role="member")
                .select_related("user")
                .first()
            )
            if chat_member:
                return UserShortInfoSerializer(chat_member.user).data
            return None

        # Исключаем текущего пользователя
        sender = chat.members.exclude(id=request_user.id).first()
        if sender:
            return UserShortInfoSerializer(sender).data

        return None

    def get_organization(self, chat):
        request = self.context["request"]
        organization = chat.organization
        if organization:
            return OrganizationFinderSerializer(
                organization, context={"request": request}
            ).data

        return None


class MessageLikeSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField()

    class Meta:
        model = MessageLike
        fields = ("message", "is_liked")


class ChatMessageUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChatMessage
        fields = ("text",)


class ChatFolderSerializer(serializers.ModelSerializer):
    chats = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=MessengerChat.objects.all(),
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = ChatFolder
        fields = ("id", "title", "chats")


class ListChatFolderSerializer(serializers.ModelSerializer):
    chats = serializers.SerializerMethodField()

    class Meta:
        model = ChatFolder
        fields = ("id", "title", "chats")

    def get_chats(self, obj):
        user = self.context["request"].user

        unread_count_subquery = (
            ChatMessage.objects.filter(
                chat=OuterRef("pk"), is_read=False, sender__is_active=True
            )
            .exclude(sender=user)
            .values("chat")
            .annotate(count=Count("id"))
            .values("count")
        )

        chats = obj.chats.annotate(
            unread_messages_count=Coalesce(
                Subquery(unread_count_subquery, output_field=IntegerField()), Value(0)
            )
        ).filter(members=user)

        serializer = MessengerChatListSerializer(chats, many=True, context=self.context)
        return serializer.data


class MessengerChatUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessengerChat
        fields = ("title", "image")


class OrganizationSimpleSerializer(serializers.ModelSerializer):
    unread_messages_count = serializers.IntegerField()
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    chat_id = serializers.SerializerMethodField()
    is_members = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    blocked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "title",
            "image",
            "unread_messages_count",
            "types",
            "chat_id",
            "is_members",
            "updated_at",
            "created_at",
            "blocked_by_me",
            "is_blocked",
        )

    def get_is_blocked(self, organization: Organization):
        request = self.context.get("request")
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.is_blocked()

    def get_blocked_by_me(self, organization: Organization):
        request = self.context.get("request")
        user = request.user
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.is_blocked_by(user)

    def get_updated_at(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.updated_at if chat else None

    def get_created_at(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.created_at if chat else None

    def get_chat_id(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.id if chat else None

    def get_is_members(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return organization.memberships.filter(
            user=request.user, role__can_send_message=True
        ).exists()


class OrganizationChatDetailSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    chat_id = serializers.SerializerMethodField()
    is_members = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    wallpapers = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = (
            "id",
            "title",
            "image",
            "types",
            "description",
            "chat_id",
            "is_members",
            "wallpapers",
            "last_message",
        )

    def get_chat_id(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        chat = organization.messenger_chats.filter(members=request.user).first()
        return chat.id if chat else None

    def get_is_members(self, organization: Organization):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        return organization.memberships.filter(
            user=request.user, role__can_send_message=True
        ).exists()

    def get_last_message(self, organization: Organization):
        chat = organization.messenger_chats.filter(
            members=self.context["request"].user
        ).first()
        if not chat:
            return None
        message = chat.messages.order_by("-created_at").first()
        if message:
            return LastMessageSerializer(message, context=self.context).data
        return None

    def get_wallpapers(self, organization: Organization):
        return (
            CommentService.get_user_theme_or_default(user=self.context["request"].user)
            if self.context.get("request")
            else None
        )
