from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import JSONField
from django.db import models
from fcm_django.models import FCMDevice

from common.models import TimestampModel
from organizations.models import Organization
from project.settings.base import HOST_URL
from .constants import (get_titles_descriptions_from_type,
                        DISCOUNT_NOTIFICATION_MODE,
                        SYSTEM_NOTIFICATION_MODE, PARTNER_MODE,
                        NOTIFICATION_TYPES, SYSTEM_TYPE, PERSONAL_MODE)

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
    organization = models.ForeignKey('organizations.Organization', on_delete=models.SET_NULL, blank=True, null=True,
                                     related_name='organization_notifications')
    mode = models.ForeignKey(NotificationMode, on_delete=models.PROTECT, related_name='notifications')
    type = models.CharField(max_length=40, choices=NOTIFICATION_TYPES, default=SYSTEM_TYPE)
    extra_data = JSONField(null=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            notification_str = get_titles_descriptions_from_type(notification_type=self.type,
                                                                 extra_data=self.extra_data)
            self.title = notification_str['title']
            self.description = notification_str['description']
            self.title_ru = notification_str['title_ru']
            self.description_ru = notification_str['description_ru']
        super().save(*args, **kwargs)

        self.send_notification(
            user=self.recipient,
            type=self.type,
            title=self.title,
            title_ru=self.title_ru,
            description=self.description,
            description_ru=self.description_ru,
            mode=self.mode.name,
            notification_id=self.id,
            organization=self.organization,
            extra_data=self.extra_data
        )

    @classmethod
    def send_notification(cls, user: User, title: str, title_ru: str, description: str, description_ru: str,
                          notification_id: int, mode: str, type: str, organization=None, extra_data=None):

        if not NotificationSetting.objects.filter(user=user).exists():
            return

        notification_setting = NotificationSetting.objects.get(user=user)

        if not ((mode == DISCOUNT_NOTIFICATION_MODE and notification_setting.discount_notifications) or (
                mode == PERSONAL_MODE and notification_setting.private_notifications) or (
                        mode == SYSTEM_NOTIFICATION_MODE and notification_setting.private_notifications) or (
                        mode == PARTNER_MODE and notification_setting.organization_notifications)):
            return

        notification_payload = {
            'title': title,
            'body': description,
            'click_action': type,
            'data': {
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'image': cls.get_organization_small_image(organization=organization) if organization else None,
                'extra_data': extra_data,
                'type': type
            },
            'icon': cls.get_organization_small_image(organization=organization) if organization else None
        }
        notification_payload_ru = {
            'title': title_ru,
            'body': description_ru,
            'click_action': type,
            'data': {
                'notification_id': notification_id,
                'organization': {
                    'id': organization.id,
                    'title': organization.title
                } if organization else None,
                'image': cls.get_organization_small_image(organization=organization) if organization else None,
                'extra_data': extra_data,
                'type': type
            },
            'icon': cls.get_organization_small_image(organization=organization) if organization else None
        }

        fcm_devices_ru = notification_setting.fcm_device.filter(settingstotoken__language='ru')
        fcm_devices_ru.send_message(**notification_payload_ru)
        fcm_devices_en = notification_setting.fcm_device.filter(settingstotoken__language='en')
        fcm_devices_en.send_message(**notification_payload)

    @staticmethod
    def get_organization_small_image(organization):
        return HOST_URL + str(organization.image.medium) if organization.image else None


class NotificationSetting(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fcm_device = models.ManyToManyField(FCMDevice, through='SettingsToToken')
    discount_notifications = models.BooleanField(default=True)
    private_notifications = models.BooleanField(default=True)
    organization_notifications = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user.phone_number)


class SettingsToToken(TimestampModel):
    ENGLISH = 'en'
    RUSSIAN = 'ru'
    TURKISH = 'tr'
    LANGUAGES = (
        (ENGLISH, ENGLISH),
        (RUSSIAN, RUSSIAN),
        (TURKISH, TURKISH)
    )
    notification_settings = models.ForeignKey(NotificationSetting, on_delete=models.CASCADE)
    fcm_device = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)
    language = models.CharField(max_length=25, choices=LANGUAGES, default=RUSSIAN)
