from django.contrib.auth import get_user_model
from django.db import models
from fcm_django.models import FCMDevice

from common.models import TimestampModel
from organizations.models import Organization
from organizations.serializers.organization_serializers import OrganizationShortInfoSerializer
from .constants import (
    NOTIFICATION_MODES,
    DISCOUNT_NOTIFICATION_MODE,
    SUBSCRIPTION_NOTIFICATION_MODE,
    SYSTEM_NOTIFICATION_MODE, PARTNER_MODE,
    NOTIFICATION_TYPES, SYSTEM_TYPE)

User = get_user_model()


class NotificationMode(TimestampModel):
    name = models.CharField(max_length=255, primary_key=True)

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
    type = models.CharField(max_length=40, choices=NOTIFICATION_TYPES, default=SYSTEM_TYPE)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super(Notification, self).save(*args, *kwargs)

        self.send_notification(
            user=self.recipient,
            title=self.title,
            description=self.description,
            mode=self.mode.name,
            notification_id=self.id,
            organization=self.organization
        )

    @classmethod
    def send_notification(cls, user: User, title: str, description: str, notification_id: int, mode: str,
                          organization=None):
        notification_setting = NotificationSetting.objects.get(user=user)
        fcm_device = notification_setting.fcm_device

        notification_payload = {
            'title': title,
            'body': description,
            'data': {
                'notification_id': notification_id,
                'organization': OrganizationShortInfoSerializer(organization, many=False).data if organization else None
            },
            'icon': cls.get_organization_small_image(organization=organization) if organization else None
        }

        if mode == DISCOUNT_NOTIFICATION_MODE and notification_setting.discount_notifications:
            fcm_device.send_message(**notification_payload)

        if mode == SUBSCRIPTION_NOTIFICATION_MODE and notification_setting.private_notifications:
            fcm_device.send_message(**notification_payload)

        if mode == SYSTEM_NOTIFICATION_MODE and notification_setting.private_notifications:
            fcm_device.send_message(**notification_payload)

        if mode == PARTNER_MODE and notification_setting.organization_notifications:
            fcm_device.send_message(**notification_payload)

    @staticmethod
    def get_organization_small_image(organization):
        return str(organization.image.medium) if organization.image else None


class NotificationSetting(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fcm_device = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)
    discount_notifications = models.BooleanField(default=True)
    private_notifications = models.BooleanField(default=True)
    organization_notifications = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user.phone_number)
