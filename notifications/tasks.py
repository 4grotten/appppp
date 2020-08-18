from typing import Union

from celery import shared_task

from common.exceptions import ObjectNotFoundException
from notifications.services import NotificationService
from organizations.models import Organization, Subscription, Membership
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
def send_notifications_organization_members(members_organization_id: int, organization_id=None,
                                            sender_id: Union[int, None] = None, mode='system',
                                            notification_type='', with_permissions=None,
                                            title='', description='',
                                            extra_data=None):
    organization = Organization.objects.get(id=organization_id)
    members_organization = Organization.objects.get(id=members_organization_id)
    owner = members_organization.owner
    sender = sender_id
    recipients = []
    members = User.objects.filter(memberships__organization_id=members_organization_id)
    if with_permissions is not None:
        if with_permissions['can_edit_partner']:
            recipients = members.filter(memberships__role__can_edit_partner=True)
    if sender_id:
        sender = User.objects.get(id=sender_id)
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
    if owner not in recipients:
        NotificationService.create_notification(
            recipient=owner,
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
        if not extra_data:
            extra_data = dict()
            can_send_message = user_can_send_message(user=recipient, organization_id=organization_id)
            extra_data['can_send_message'] = can_send_message

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


def user_can_send_message(organization_id: int, user: User) -> bool:
    try:
        organization = Organization.objects.get(id=organization_id)
    except Organization.DoesNotExist:
        raise ObjectNotFoundException
    if organization.owner == user:
        return True
    try:
        membership = Membership.objects.get(organization=organization, user=user)
    except Membership.DoesNotExist:
        return False
    return membership.role.can_send_message
