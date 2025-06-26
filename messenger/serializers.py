from datetime import timedelta

from instagrapi.types import UserShort
from rest_framework import serializers

from messenger.models import MessengerChat, ChatMessage
from messenger.services import MessengerChatService
from users.serializers import UserShortInfoSerializer


class MessengerChatSerializer(serializers.ModelSerializer):
    members = UserShortInfoSerializer(many=True, read_only=True)

    class Meta:
        model = MessengerChat
        fields = ('id', 'chat_type', 'title', 'members')


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