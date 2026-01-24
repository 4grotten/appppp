from django.urls import path
from messenger_bots.views import (
    TelegramWebhookView,
    WhatsAppWebhookView,
    WAHAWebhookView,
    TelegramBotAPIView,
    TelegramBotSettingsAPIView,
    WhatsAppBotAPIView,
    WhatsAppWAHABotAPIView,
    WhatsAppWAHASessionAPIView,
    WhatsAppWAHAQRCodeAPIView,
    WhatsAppRebindAPIView,
    BotChatsAPIView,
    BotChatMessagesAPIView,
    BotStatusAPIView,
    BotUnreadCountAPIView,
    AutoCreateTelegramBotAPIView,
    BotCreationStatusAPIView,
)

urlpatterns = [
    # Webhook endpoints (no auth)
    path(
        "telegram/webhook/<int:organization_id>/",
        TelegramWebhookView.as_view(),
        name="telegram-webhook",
    ),
    path(
        "whatsapp/webhook/<int:organization_id>/",
        WhatsAppWebhookView.as_view(),
        name="whatsapp-webhook",
    ),
    # WAHA global webhook (extracts org from session name)
    path(
        "whatsapp/waha/webhook/",
        WAHAWebhookView.as_view(),
        name="waha-webhook",
    ),

    # Bot management API (auth required)
    path(
        "telegram/<int:organization_id>/",
        TelegramBotAPIView.as_view(),
        name="telegram-bot",
    ),
    path(
        "telegram/<int:organization_id>/settings/",
        TelegramBotSettingsAPIView.as_view(),
        name="telegram-bot-settings",
    ),
    # Meta Cloud API WhatsApp
    path(
        "whatsapp/<int:organization_id>/",
        WhatsAppBotAPIView.as_view(),
        name="whatsapp-bot",
    ),
    # WAHA WhatsApp
    path(
        "whatsapp/waha/<int:organization_id>/",
        WhatsAppWAHABotAPIView.as_view(),
        name="whatsapp-waha-bot",
    ),
    path(
        "whatsapp/waha/<int:organization_id>/session/",
        WhatsAppWAHASessionAPIView.as_view(),
        name="whatsapp-waha-session",
    ),
    path(
        "whatsapp/waha/<int:organization_id>/session/rebind/",
        WhatsAppRebindAPIView.as_view(),
        name="whatsapp-waha-rebind",
    ),
    path(
        "whatsapp/waha/<int:organization_id>/qr/",
        WhatsAppWAHAQRCodeAPIView.as_view(),
        name="whatsapp-waha-qr",
    ),

    # Auto-create bot (one-click)
    path(
        "telegram/auto-create/<int:organization_id>/",
        AutoCreateTelegramBotAPIView.as_view(),
        name="telegram-bot-auto-create",
    ),
    path(
        "creation-status/<int:request_id>/",
        BotCreationStatusAPIView.as_view(),
        name="bot-creation-status",
    ),

    # Bot status
    path(
        "status/<int:organization_id>/",
        BotStatusAPIView.as_view(),
        name="bot-status",
    ),
    # Unread count (for menu badge)
    path(
        "unread/<int:organization_id>/",
        BotUnreadCountAPIView.as_view(),
        name="bot-unread-count",
    ),

    # Chats
    path(
        "chats/<int:organization_id>/",
        BotChatsAPIView.as_view(),
        name="bot-chats",
    ),
    path(
        "chats/<int:chat_id>/messages/",
        BotChatMessagesAPIView.as_view(),
        name="bot-chat-messages",
    ),
]
