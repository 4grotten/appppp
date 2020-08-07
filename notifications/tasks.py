import celery
from django.contrib.auth import get_user_model
from notifications.constants import (
    SUBSCRIPTION_NOTIFICATION_MODE, NEW_ORGANIZATION,
    NEW_ORGANIZATION_TITLE, SYSTEM_NOTIFICATION_MODE
)
from notifications.services import NotificationService
from organizations.models import Organization

User = get_user_model()


@celery.shared_task
def send_notifications_to_all_users(organization_id: int, user_id: int):
    users = User.objects.exclude(id=user_id)
    organization = Organization.objects.get(id=organization_id)

    for user in users:
        NotificationService.create_notification(
            recipient=user,
            mode=SYSTEM_NOTIFICATION_MODE,
            notification_type=NEW_ORGANIZATION,
            title=NEW_ORGANIZATION_TITLE,
            description=organization.address,
            organization=organization
        )


@celery.shared_task
def sent_notification(recipient_id: int, sender_id=None, mode='system', notification_type='system', extra_data=None,
                      title='Title was not sent', description='Description was not sent', organization_id=None):
    if recipient_id is not None:
        recipient = User.objects.get(id=recipient_id)
    else:
        recipient = None
    if sender_id is not None:
        sender = User.objects.get(id=sender_id)
    else:
        sender = None
    if organization_id is not None:
        organization = Organization.objects.get(id=organization_id)
    else:
        organization = None

    NotificationService.create_notification(
        recipient=recipient,
        sender=sender,
        mode=mode,
        notification_type=notification_type,
        title=title,
        description=description,
        organization=organization,
        extra_data=extra_data
    )
