from datetime import timedelta

from instagrapi.types import UserShort
from rest_framework import serializers

from messenger.models import MessengerChat, ChatMessage, MessageLike
from messenger.services import MessengerChatService
from users.serializers import UserShortInfoSerializer


class MessengerChatSerializer(serializers.ModelSerializer):
    is_blocked = serializers.SerializerMethodField()
    blocked_by_me = serializers.SerializerMethodField()
    members = UserShortInfoSerializer(many=True, read_only=True)

    class Meta:
        model = MessengerChat
        fields = ('id', 'chat_type', 'title', 'members', 'is_blocked', 'blocked_by_me')

    def get_is_blocked(self, chat):
        return chat.is_blocked()

    def get_blocked_by_me(self, chat):
        request = self.context.get('request')
        return chat.is_blocked_by(request.user) if request else False


class ParentChatMessageSerializer(serializers.ModelSerializer):
    user = UserShortInfoSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ('id', 'user', 'text')


class ChatMessageSerializer(serializers.ModelSerializer):
    is_message_liked = serializers.SerializerMethodField()
    sender = UserShortInfoSerializer(read_only=True)
    message_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = ParentChatMessageSerializer()
    is_updated = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = (
            'id', 'sender', 'parent', 'text', 'is_message_liked', 'message_like_count', 'can_delete', 'is_updated',
            'status', 'created_at', 'updated_at'
        )

    def get_is_updated(self, message: ChatMessage) -> bool:
        return (message.updated_at - message.created_at) > timedelta(seconds=1)

    def get_can_delete(self, message: ChatMessage) -> bool:
        user = self.context['request'].user
        return user == message.sender

    def get_is_message_liked(self, message: ChatMessage) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return MessengerChatService.is_message_liked_by_user(message=message, user=user)

    def get_message_like_count(self, message: ChatMessage) -> int:
        return message.likes.count()

    def get_status(self, message: ChatMessage) -> str:
        if message.is_read:
            return 'read'
        elif message.is_delivered:
            return 'delivered'
        elif message.is_sent:
            return 'sent'
        return 'pending'


class ChatMessageWSSerializer(serializers.ModelSerializer):
    is_message_liked = serializers.SerializerMethodField()
    sender = UserShortInfoSerializer(read_only=True)
    message_like_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    parent = ParentChatMessageSerializer()
    is_updated = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = (
            'id', 'sender', 'parent', 'text', 'is_message_liked', 'message_like_count', 'can_delete', 'is_updated',
            'status', 'created_at', 'updated_at'
        )

    def get_is_updated(self, message: ChatMessage) -> bool:
        return (message.updated_at - message.created_at) > timedelta(seconds=1)

    def get_can_delete(self, message: ChatMessage) -> bool:
        user = self.context.get('user')
        return user == message.sender

    def get_is_message_liked(self, message: ChatMessage) -> bool:
        user = self.context.get('user')
        if not user.is_authenticated:
            return False
        return MessengerChatService.is_message_liked_by_user(message=message, user=user)

    def get_message_like_count(self, message: ChatMessage) -> int:
        return message.likes.count()

    def get_status(self, message: ChatMessage) -> str:
        if message.is_read:
            return 'read'
        elif message.is_delivered:
            return 'delivered'
        elif message.is_sent:
            return 'sent'
        return 'pending'


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('parent', 'text')

    def validate(self, attrs):
        user = self.context.get('user')
        if not user or not user.is_authenticated:
            raise serializers.ValidationError('User is not authenticated')
        attrs['user'] = user
        return attrs


class LastMessageSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ('id', 'text', 'created_at', 'status', 'is_mine')

    def get_status(self, obj: ChatMessage):
        if obj.is_read:
            return 'read'
        elif obj.is_delivered:
            return 'delivered'
        elif obj.is_sent:
            return 'sent'
        return 'pending'

    def get_is_mine(self, obj: ChatMessage):
        request = self.context.get('request')
        return obj.sender == request.user if request else False


class MessengerChatListSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()
    blocked_by_me = serializers.SerializerMethodField()
    sender = serializers.SerializerMethodField()

    class Meta:
        model = MessengerChat
        fields = ('id', 'sender', 'chat_type', 'title', 'last_message', 'is_blocked', 'blocked_by_me')

    def get_last_message(self, chat):
        message = chat.messages.order_by('-created_at').first()
        if message:
            return LastMessageSerializer(message, context=self.context).data
        return None

    def get_is_blocked(self, chat):
        return chat.is_blocked()

    def get_blocked_by_me(self, chat):
        user = self.context['request'].user
        return chat.is_blocked_by(user)

    def get_sender(self, chat):
        request_user = self.context['request'].user
        if chat.chat_type == MessengerChat.PRIVATE:
            sender = chat.members.exclude(id=request_user.id).first()
            if sender:
                return UserShortInfoSerializer(sender).data
        return None


class MessageLikeSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField()

    class Meta:
        model = MessageLike
        fields = ('message', 'is_liked')