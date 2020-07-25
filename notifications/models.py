from django.contrib.auth import get_user_model
from django.db import models
from fcm_django.models import FCMDevice

from common.models import TimestampModel
from .constants import NOTIFICATION_MODES
from .services import NotificationSettingService

User = get_user_model()


class Notification(TimestampModel):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipient_notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True,
                               related_name='sender_notifications')
    mode = models.CharField(max_length=20, choices=NOTIFICATION_MODES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super(Notification, self).save(*args, *kwargs)

        NotificationSettingService.send_notification(
            user=self.recipient,
            title=self.title,
            description=self.description,
            mode=self.mode,
            notification_id=self.id
        )


class NotificationSetting(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fcm_device = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)
    discount_notifications = models.BooleanField(default=True)
    private_notifications = models.BooleanField(default=True)
    organization_notifications = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user.phone_number)
