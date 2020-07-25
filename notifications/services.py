from django.contrib.auth import get_user_model
from fcm_django.models import FCMDevice

from common.exceptions import ObjectNotFoundException, IntegrityException
from .constants import (
    DISCOUNT_NOTIFICATION_MODE,
    SUBSCRIPTION_NOTIFICATION_MODE,
    SYSTEM_NOTIFICATION_MODE,
    PARTNER_MODE
)
from .models import (
    Notification, NotificationSetting
)

User = get_user_model()


class NotificationService:
    model = Notification

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException('Notification not found')

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def create_notification(cls, recipient, sender: None, mode, title, description):
        try:
            return cls.model.objects.create(
                recipient=recipient,
                sender=sender,
                mode=mode,
                title=title,
                description=description
            )
        except Exception as e:
            raise IntegrityException('Error while creating notification: {e}'.format(e=str(e)))

    @classmethod
    def get_own_notifications(cls, user: User):
        return cls.filter(recipient=user)


class NotificationSettingService:
    model = NotificationSetting

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException('Settings not found')

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def get_fcm_device(cls, user: User) -> FCMDevice:
        setting = cls.get(user=user)

        return setting.fcm_device

    @classmethod
    def send_notification(cls, user: User, title: str, description: str, notification_id: int, mode: str):
        notification_setting = cls.get(user=user)
        fcm_device = notification_setting.fcm_device

        notification_payload = {
            'title': title,
            'body': description,
            'data': {
                'notification_id': notification_id
            }
        }

        if mode == DISCOUNT_NOTIFICATION_MODE and notification_setting.discount_notifications:
            fcm_device.send_message(**notification_payload)

        if mode == SUBSCRIPTION_NOTIFICATION_MODE and notification_setting.private_notifications:
            fcm_device.send_message(**notification_payload)

        if mode == SYSTEM_NOTIFICATION_MODE and notification_setting.private_notifications:
            fcm_device.send_message(**notification_payload)

        if mode == PARTNER_MODE and notification_setting.organization_notifications:
            fcm_device.send_message(**notification_payload)
