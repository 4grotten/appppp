from django.contrib.auth import get_user_model

from common.exceptions import ObjectNotFoundException, IntegrityException
from notifications.models import Notification

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
