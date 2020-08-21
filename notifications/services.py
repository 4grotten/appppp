from django.contrib.auth import get_user_model
from django.db import IntegrityError

from common.exceptions import ObjectNotFoundException, IntegrityException
from .models import (
    Notification,
    NotificationSetting,
    NotificationMode)

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
    def create_notification(cls, recipient, mode, title, description, notification_type, organization=None,
                            sender=None, extra_data=None):
        try:

            mode_object = NotificationMode.objects.get(name=mode)  # move to services

            notification, _ = cls.model.objects.get_or_create(
                recipient=recipient,
                sender=sender,
                mode=mode_object,
                title=title,
                description=description,
                organization=organization,
                type=notification_type,
                extra_data=extra_data
            )

            return notification
        except Exception as e:
            raise IntegrityException('Error while creating notification: {e}'.format(e=str(e)))

    @classmethod
    def get_own_notifications(cls, user: User):
        return cls.filter(recipient=user, organization__isnull=False)

    @classmethod
    def get_user_notifications_count(cls, user: User):
        return cls.filter(is_read=False, recipient=user).count()

    @classmethod
    def do_read_notifications(cls, user: User):
        return cls.filter(is_read=False, recipient=user).update(is_read=True)


class NotificationSettingService:
    model = NotificationSetting

    @classmethod
    def get_or_create(cls, user: User):
        try:
            settings, _ = NotificationSetting.objects.get_or_create(user=user)
            return settings
        except IntegrityError:
            raise IntegrityException('Settings not found')

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

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
