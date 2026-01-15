from rest_framework import serializers
from messenger_bots.models import (
    TelegramBot,
    WhatsAppBot,
    WhatsAppProvider,
    WhatsAppSessionStatus,
    BotChat,
    BotMessage,
    BotCreationRequest,
)


class TelegramBotSerializer(serializers.ModelSerializer):
    """Serializer for Telegram bot configuration (read)."""

    organization_id = serializers.IntegerField(source="organization.id", read_only=True)
    organization_title = serializers.CharField(source="organization.title", read_only=True)

    class Meta:
        model = TelegramBot
        fields = [
            "id",
            "organization_id",
            "organization_title",
            "bot_username",
            "is_active",
            "webhook_url",
            "last_error",
            "created_at",
            "updated_at",
        ]


class TelegramBotCreateSerializer(serializers.Serializer):
    """Serializer for creating/updating Telegram bot."""

    bot_token = serializers.CharField(max_length=100)
    is_active = serializers.BooleanField(default=True)

    def validate_bot_token(self, value):
        """Validate bot token format."""
        if ":" not in value:
            raise serializers.ValidationError(
                "Invalid bot token format. Token should be in format: 123456789:ABCdefGHI..."
            )
        return value


class WhatsAppBotSerializer(serializers.ModelSerializer):
    """Serializer for WhatsApp bot configuration (read)."""

    organization_id = serializers.IntegerField(source="organization.id", read_only=True)
    organization_title = serializers.CharField(source="organization.title", read_only=True)
    provider_display = serializers.CharField(source="get_provider_display", read_only=True)
    session_status_display = serializers.CharField(source="get_session_status_display", read_only=True)
    is_connected = serializers.BooleanField(read_only=True)

    class Meta:
        model = WhatsAppBot
        fields = [
            "id",
            "organization_id",
            "organization_title",
            "provider",
            "provider_display",
            # WAHA fields
            "waha_session_name",
            "session_status",
            "session_status_display",
            "connected_phone_number",
            # Meta Cloud API fields
            "phone_number_id",
            "business_account_id",
            "display_phone_number",
            "verify_token",
            # Twilio fields
            "twilio_phone_number",
            # Common fields
            "is_active",
            "is_connected",
            "last_error",
            "last_activity_at",
            "created_at",
            "updated_at",
        ]


class WhatsAppBotCreateSerializer(serializers.Serializer):
    """Serializer for creating/updating WhatsApp bot (Meta Cloud API)."""

    phone_number_id = serializers.CharField(max_length=50)
    business_account_id = serializers.CharField(max_length=50)
    access_token = serializers.CharField()
    webhook_secret = serializers.CharField(max_length=64, required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)


class WhatsAppBotWAHACreateSerializer(serializers.Serializer):
    """Serializer for creating WhatsApp bot with WAHA provider."""

    is_active = serializers.BooleanField(default=True)


class WhatsAppSessionStatusSerializer(serializers.Serializer):
    """Serializer for WhatsApp WAHA session status response."""

    session_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    qr_code = serializers.CharField(read_only=True, allow_null=True)
    connected_phone = serializers.CharField(read_only=True, allow_null=True)
    is_healthy = serializers.BooleanField(read_only=True)


class BotChatSerializer(serializers.ModelSerializer):
    """Serializer for bot chat."""

    platform_display = serializers.CharField(source="get_platform_display", read_only=True)
    messages_count = serializers.SerializerMethodField()

    class Meta:
        model = BotChat
        fields = [
            "id",
            "platform",
            "platform_display",
            "platform_chat_id",
            "user_name",
            "user_phone",
            "is_active",
            "last_message_at",
            "messages_count",
            "created_at",
        ]

    def get_messages_count(self, obj):
        return obj.messages.count()


class BotMessageSerializer(serializers.ModelSerializer):
    """Serializer for bot message."""

    sender_display = serializers.CharField(source="get_sender_display", read_only=True)

    class Meta:
        model = BotMessage
        fields = [
            "id",
            "chat_id",
            "sender",
            "sender_display",
            "text",
            "platform_message_id",
            "created_at",
        ]


class BotCreationRequestSerializer(serializers.ModelSerializer):
    """Serializer for bot creation request."""

    organization_id = serializers.IntegerField(source="organization.id", read_only=True)
    organization_title = serializers.CharField(source="organization.title", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = BotCreationRequest
        fields = [
            "id",
            "organization_id",
            "organization_title",
            "status",
            "status_display",
            "bot_name",
            "bot_username",
            "error_message",
            "created_at",
            "completed_at",
        ]
