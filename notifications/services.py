from django.contrib.auth import get_user_model
from fcm_django.models import FCMDevice

from common.exceptions import ObjectNotFoundException, IntegrityException
from .models import (
    Notification,
    NotificationSetting
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
    def create_notification(cls, recipient, mode, title, description, organization=None, sender=None):
        try:
            return cls.model.objects.create(
                recipient=recipient,
                sender=sender,
                mode=mode,
                title=title,
                description=description,
                organization=organization
            )
        except Exception as e:
            raise IntegrityException('Error while creating notification: {e}'.format(e=str(e)))

    @classmethod
    def get_own_notifications(cls, user: User):
        return cls.filter(recipient=user)

    @classmethod
    def get_user_notifications_count(cls, user: User):
        return cls.filter(is_read=False, recipient=user).count()

    @classmethod
    def do_read_notifications(cls, user: User):
        return cls.filter(is_read=False, recipient=user).update(is_read=True)


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
    def update(cls, notification_setting: NotificationSetting, discount_notifications: bool,
               private_notifications: bool, organization_notifications: bool):
        try:
            notification_setting.discount_notifications = discount_notifications
            notification_setting.private_notifications = private_notifications
            notification_setting.organization_notifications = organization_notifications
            notification_setting.save()

            return notification_setting

        except Exception as e:
            raise IntegrityException('Can not update: {e}'.format(e=str(e)))
