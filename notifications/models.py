from django.contrib.auth import get_user_model
from django.db import models
from fcm_django.models import FCMDevice

from common.models import TimestampModel
from notifications.tasks import send_notification
from organizations.models import Organization
from shop.models import ShopItem

from .constants import (
    NOTIFICATION_MODES,
    NOTIFICATION_TYPES,
    SYSTEM_TYPE,
    get_titles_descriptions_from_type,
)

User = get_user_model()


class NotificationMode(TimestampModel):
    name = models.CharField(max_length=255, primary_key=True)

    def __str__(self):
        return self.name


class Notification(TimestampModel):
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipient_notifications"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="sender_notifications",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_read = models.BooleanField(default=False)
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="organization_notifications",
    )

    item = models.ForeignKey(
        "shop.ShopItem",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="shopitem_notifications",
    )
    mode = models.CharField(max_length=255, choices=NOTIFICATION_MODES)
    type = models.CharField(
        max_length=255, choices=NOTIFICATION_TYPES, default=SYSTEM_TYPE
    )
    extra_data = models.JSONField(null=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.pk:
            notification_str = get_titles_descriptions_from_type(
                notification_type=self.type, extra_data=self.extra_data
            )
            if notification_str:
                self.title = notification_str["title"]
                self.description = notification_str["description"]
                self.title_ru = notification_str["title_ru"]
                self.description_ru = notification_str["description_ru"]
                self.title_de = notification_str["title_de"]
                self.description_de = notification_str["description_de"]
                self.title_tr = notification_str["title_tr"]
                self.description_tr = notification_str["description_tr"]
                self.title_zh = notification_str["title_zh"]
                self.description_zh = notification_str["description_zh"]
            else:
                self.title = self.title
                self.description = self.description
                self.title_ru = self.title
                self.description_ru = self.description
                self.title_de = self.title
                self.description_de = self.description
                self.title_tr = self.title
                self.description_tr = self.description
                self.title_zh = self.title
                self.description_zh = self.description
        super().save(*args, **kwargs)

        send_notification.delay(
            user=self.recipient.pk,
            type=self.type,
            title=self.title,
            title_ru=self.title_ru,
            title_de=self.title_de,
            title_tr=self.title_tr,
            title_zh=self.title_zh,
            description=self.description,
            description_ru=self.description_ru,
            description_de=self.description_de,
            description_tr=self.description_tr,
            description_zh=self.description_zh,
            mode=self.mode,
            notification_id=self.id,
            organization=self.organization,
            item=self.item,
            extra_data=self.extra_data,
        )

    @staticmethod
    def convert_to_string_dict(data):
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
        return ""

    @staticmethod
    def get_organization_small_image(organization: Organization):
        return organization.image.medium.url if organization.image else None

    @staticmethod
    def get_item_small_image(item: ShopItem):
        return item.images.first().medium.url if item else None


# FIXME: Add type field and get rid of 5 diffrent types of notifications.
class NotificationSetting(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fcm_device = models.ManyToManyField(FCMDevice, through="SettingsToToken")
    discount_notifications = models.BooleanField(default=True)
    private_notifications = models.BooleanField(default=True)
    organization_notifications = models.BooleanField(default=False)
    product_notifications = models.BooleanField(default=True)
    delivery_notifications = models.BooleanField(default=True)
    rental_notifications = models.BooleanField(default=True)
    ticket_notifications = models.BooleanField(default=True)
    resume_notifications = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user.phone_number)


class SettingsToToken(TimestampModel):
    ENGLISH = "en"
    RUSSIAN = "ru"
    TURKISH = "tr"
    GERMAN = "de"
    CHINESE = "zh"
    LANGUAGES = (
        (ENGLISH, ENGLISH),
        (RUSSIAN, RUSSIAN),
        (TURKISH, TURKISH),
        (GERMAN, GERMAN),
        (CHINESE, CHINESE),
    )
    notification_settings = models.ForeignKey(
        NotificationSetting, on_delete=models.CASCADE
    )
    fcm_device = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)
    language = models.CharField(max_length=25, choices=LANGUAGES, default=RUSSIAN)
