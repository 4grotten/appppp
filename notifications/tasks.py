from typing import Union

from celery import shared_task
from django.db.models import Q

from common.exceptions import ObjectNotFoundException
from notifications import constants
from notifications.services import NotificationService
from organizations.models import Organization, Subscription, Membership
from shop.models import Cart, ShopItem
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
                                            notification_type='was not sent', with_permissions=None,
                                            title='was not sent', description='was not sent', exclusion=[],
                                            extra_data=None):
    organization = Organization.objects.get(id=organization_id)
    members_organization = Organization.objects.get(id=members_organization_id)
    owner = members_organization.owner
    sender = sender_id
    if sender_id:
        sender = User.objects.get(id=sender_id)

    recipients = User.objects.filter(memberships__organization_id=members_organization_id).exclude(
        id__in=exclusion).distinct()
    if with_permissions is not None:
        can_edit_partner = with_permissions.get('can_edit_partner')
        if can_edit_partner:
            recipients = recipients.filter(memberships__role__can_edit_partner=True,
                                           memberships__organization_id=members_organization_id).exclude(
                id__in=exclusion)

        can_send_message = with_permissions.get('can_send_message')
        if can_send_message:
            recipients = recipients.filter(memberships__role__can_send_message=True,
                                           memberships__organization_id=members_organization_id).exclude(
                id__in=exclusion)
        can_edit_organization = with_permissions.get('can_edit_organization')
        if can_edit_organization:
            recipients = recipients.filter(memberships__role__can_edit_organization=True,
                                           memberships__organization_id=members_organization_id).exclude(
                id__in=exclusion)
        can_see_stats = with_permissions.get('can_see_stats')
        if can_see_stats:
            recipients = recipients.filter(memberships__role__can_see_stats=True,
                                           memberships__organization_id=members_organization_id).exclude(
                id__in=exclusion)

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
def send_notifications_to_deliverers(cart_id, sender_id: Union[int, None] = None,
                                     mode=constants.NOTIFICATION_MODE_SYSTEM,
                                     notification_type=constants.NOTIFICATION_TYPE_AVAILABLE_DELIVERY,
                                     title='Title was not sent', description='Description was not sent',
                                     extra_data=None):
    sender = sender_id
    if sender_id:
        sender = User.objects.get(id=sender_id)

    cart = Cart.objects.get(pk=cart_id)
    organization = cart.organization
    country = cart.organization.country
    city = cart.organization.city
    recipients = User.objects.filter(
        owned_organizations__is_delivery_service=True,
        owned_organizations__country=country,
        owned_organizations__is_active=True,
        owned_organizations__is_banned=False,
        owned_organizations__is_deleted=False,
        # memberships__organization__is_delivery_service=True,
    ).distinct()
    staff_recipients = User.objects.filter(
        Q(memberships__organization__country=country,
          memberships__organization__is_active=True,
          memberships__organization__is_banned=False,
          memberships__organization__is_deleted=False,
          memberships__organization__is_delivery_service=True,
          ) &
        Q(
            Q(memberships__role__can_see_stats=True) |
            Q(memberships__role__can_edit_organization=True) |
            Q(memberships__role__can_deliver=True)
        )

    ).distinct()
    extra_data = {
        'organization': organization.title,
        'final_price': str(cart.transaction.final_amount),
        'currency': cart.transaction.currency.code,
        'who_pays': cart.transaction.delivery_info.who_pays,
        'transaction_id': cart.transaction.id,
        'delivery_amount': str(cart.transaction.delivery_info.amount),
        'delivery_currency': str(cart.transaction.delivery_info.currency.code),
        'delivery_organization_id': None,
        'delivery_organization_title': None,
        'delivery_organization': None,
        'delivery_organization_image': None,

    }

    for recipient in list(recipients):
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

    for recipient in list(staff_recipients):
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
def send_delivery_notitication_to_organization_or_client(recipient, cart_id, notification_type,
                                                         sender_id: Union[int, None] = None,
                                                         mode=constants.NOTIFICATION_MODE_PRODUCT,
                                                         title='Title was not sent',
                                                         description='Description was not sent', extra_data=None):
    sender = sender_id
    if sender_id:
        sender = User.objects.get(id=sender_id)
    cart = Cart.objects.get(pk=cart_id)
    organization = cart.organization

    delivery_organization = cart.transaction.delivery_info.delivery_organization

    extra_data = {
        'organization': organization.title,
        'delivery_organization_id': delivery_organization.id if delivery_organization else None,
        'delivery_organization_title': delivery_organization.title if delivery_organization else None,
        'delivery_organization': delivery_organization.title if delivery_organization else None,
        'delivery_organization_image': delivery_organization.image.small.url if delivery_organization else None,
        'final_price': str(cart.transaction.final_amount),
        'original_price': str(cart.transaction.original_amount),
        'currency': cart.transaction.currency.code,
        'who_pays': cart.transaction.delivery_info.who_pays,
        'transaction_id': cart.transaction.id,
        'delivery_amount': str(cart.transaction.delivery_info.amount),

    }
    try:
        extra_data['delivery_currency'] = str(cart.transaction.delivery_info.currency.code)
    except AttributeError:
        extra_data['delivery_currency'] = str(cart.transaction.currency.code)

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
                      title='Title was not sent', description='Description was not sent', organization_id=None,
                      item_id=None):
    recipient = User.objects.get(id=recipient_id)
    if sender_id is not None:
        sender = User.objects.get(id=sender_id)
    else:
        sender = None
    if organization_id is not None:
        organization = Organization.objects.get(id=organization_id)
    else:
        organization = None
    if item_id is not None:
        item = ShopItem.objects.get(id=item_id)
    else:
        item = None

    NotificationService.create_notification(
        recipient=recipient,
        sender=sender,
        mode=mode,
        notification_type=notification_type,
        title=title,
        description=description,
        organization=organization,
        item=item,
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
