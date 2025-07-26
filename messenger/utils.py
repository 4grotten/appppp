from firebase_admin.messaging import Message, Notification as FCMNotification
from messenger.constants import (
    TRANSLATIONS,
)
from messenger.models import ChatMessage
from notifications.models import NotificationSetting
from users.models import User
from django.conf import settings
from asgiref.sync import async_to_sync, sync_to_async
from channels.layers import get_channel_layer


def send_push_message_chat(
    user: User,
    title: str,
    body: str,
    text: str = None,
    image: str = None,
    chat_id: int = None,
    is_group: bool = False,
):
    """
    Отправка push-уведомления чата пользователю.
    """
    data = {
        "user_id": str(user.id),
        "is_group": str(is_group).lower(),
    }
    if chat_id is not None:
        data["chat_id"] = str(chat_id)
    if text is not None:
        data["text"] = text
    if image is not None:
        data["icon"] = image
    push_message = Message(
        notification=FCMNotification(title=title, body=body, image=None), data=data
    )
    notification_setting = NotificationSetting.objects.filter(user=user).first()
    if not notification_setting:
        return
    fcm_devices = notification_setting.fcm_device.all()
    if not fcm_devices:
        return

    fcm_devices.send_message(push_message, dry_run=settings.FCM_DRY_RUN_ENABLE)


def get_chat_translation(action: str, lang: str, is_group: bool) -> str:
    lang = lang.lower()
    chat_type = "group" if is_group else "private"
    return (
        TRANSLATIONS.get(action, {})
        .get(chat_type, {})
        .get(lang, TRANSLATIONS.get(action, {}).get(chat_type, {}).get("en", ""))
    )


def send_unread_message_count_via_ws(user):
    unread_count = (
        ChatMessage.objects.filter(is_read=False, chat__members=user)
        .exclude(sender=user)
        .count()
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}_unread_messages",
        {
            "type": "send_unread_count",
            "count": unread_count,
        },
    )


async def send_unread_message_count_via_ws_async(user):
    unread_count = await sync_to_async(
        lambda: ChatMessage.objects.filter(is_read=False, chat__members=user)
        .exclude(sender=user)
        .count()
    )()

    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{user.id}_unread_messages",
        {
            "type": "send_unread_count",
            "count": unread_count,
        },
    )
