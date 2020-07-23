from django.contrib.auth import get_user_model
from django.db import models
from fcm_django.models import FCMDevice

from common.exceptions import ObjectNotFoundException
from common.models import TimestampModel
from notifications.constants import NOTIFICATION_MODES

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
        fcm_device = self.get_fcm_device()
        self.send_notification(fcm_device=fcm_device)

    def get_fcm_device(self):
        try:
            return FCMDevice.objects.get(user=self.recipient)
        except FCMDevice.DoesNotExist:
            raise ObjectNotFoundException('FCM device not found')

    def send_notification(self, fcm_device):
        fcm_device.send_message(
            title=self.title,
            body=self.description,
            data={
                "notification_id": self.id
            }
        )


class NotificationSetting(TimestampModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fcm_device = models.ForeignKey(FCMDevice, on_delete=models.CASCADE)
    discount_notifications = models.BooleanField(default=True)
    private_notifications = models.BooleanField(default=True)
    organization_notifications = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user.phone_number)
