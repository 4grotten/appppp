from typing import Union

from celery import shared_task
from notifications.services import NotificationService
from organizations.models import Organization, Subscription
from users.models import User


@shared_task
def send_notifications_to_all_users(sender_id: Union[int, None] = None, mode='system', notification_type='system',
                                    title='Title was not sent', description='Description was not sent',
                                    extra_data=None, organization_id=None):
    recipients = User.objects.all()
    sender = sender_id
    if sender_id:
        sender = User.objects.get(id=sender_id)
    organization = Organization.objects.get(id=organization_id)
    for recipient in recipients:
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


@shared_task
def send_notifications_to_subscribers(sender_id: Union[int, None] = None, mode='system', notification_type='system',
                                      title='Title was not sent', description='Description was not sent',
                                      extra_data=None, organization_id=None):
    sender = sender_id
    if sender_id:
        sender = User.objects.get(id=sender_id)
    recipients = User.objects.filter(subscriptions__organization_id=organization_id)
    organization = Organization.objects.get(id=organization_id)
    for recipient in recipients:
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


@shared_task
def sent_notification(recipient_id: int, sender_id=None, mode='system', notification_type='system', extra_data=None,
                      title='Title was not sent', description='Description was not sent', organization_id=None):
    recipient = User.objects.get(id=recipient_id)
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
