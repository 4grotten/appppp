from django.contrib.auth import get_user_model
from django.db import models
from fcm_django.models import FCMDevice

from common.models import TimestampModel
from organizations.models import Organization
from .constants import (
    NOTIFICATION_MODES,
    DISCOUNT_NOTIFICATION_MODE,
    SUBSCRIPTION_NOTIFICATION_MODE,
    SYSTEM_NOTIFICATION_MODE, PARTNER_MODE
)

User = get_user_model()


class NotificationMode(TimestampModel):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=NOTIFICATION_MODES)

    def __str__(self):
        return self.name


class Notification(TimestampModel):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipient_notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                               related_name='sender_notifications')
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_read = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, blank=True, null=True,
                                     related_name='organization_notifications')
    mode = models.ForeignKey(NotificationMode, on_delete=models.PROTECT, related_name='notifications')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super(Notification, self).save(*args, *kwargs)

        self.send_notification(
            user=self.recipient,
            title=self.title,
            description=self.description,
            mode=self.mode.name,
            notification_id=self.id
        )

    @staticmethod
    def send_notification(user: User, title: str, description: str, notification_id: int, mode: str):
        notification_setting = NotificationSetting.objects.get(user=user)
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


class NotificationSetting(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fcm_device = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)
    discount_notifications = models.BooleanField(default=True)
    private_notifications = models.BooleanField(default=True)
    organization_notifications = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user.phone_number)
