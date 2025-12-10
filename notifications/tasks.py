from typing import Union

from celery import shared_task
from django.conf import settings
from django.db.models import Q
from firebase_admin.messaging import Message

from common.exceptions import ObjectNotFoundException
from notifications import constants
from notifications.constants import (
    NOTIFICATION_MODE_DISCOUNT,
    NOTIFICATION_MODE_PARTNER,
    NOTIFICATION_MODE_PERSONAL,
    NOTIFICATION_MODE_PRODUCT,
    NOTIFICATION_MODE_RENTAL,
    NOTIFICATION_MODE_RESUME,
    NOTIFICATION_MODE_SYSTEM,
    NOTIFICATION_MODE_TICKET,
    NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
)
from notifications.models import NotificationSetting
from notifications.services import NotificationService
from organizations.models import Membership, Organization
from shop.models import Cart, ShopItem
from transactions.models import Transaction
from users.models import User


@shared_task
def send_notifications_to_all_users(
    sender_id: Union[int, None] = None,
    mode="system",
    notification_type="system",
    title="Title was not sent",
    description="Description was not sent",
    extra_data=None,
    organization_id=None,
):
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
            extra_data=extra_data,
        )


@shared_task
def send_notifications_organization_members(
    members_organization_id: int,
    organization_id=None,
    sender_id: Union[int, None] = None,
    mode="system",
    notification_type="was not sent",
    with_permissions=None,
    title="was not sent",
    description="was not sent",
    exclusion=[],
    extra_data=None,
):
    organization = Organization.objects.get(id=organization_id)
    members_organization = Organization.objects.get(id=members_organization_id)
    owner = members_organization.owner
    sender = sender_id
    if sender_id:
        sender = User.objects.get(id=sender_id)

    recipients = (
        User.objects.filter(memberships__organization_id=members_organization_id)
        .exclude(id__in=exclusion)
        .distinct()
    )
    if with_permissions is not None:
        can_edit_partner = with_permissions.get("can_edit_partner")
        if can_edit_partner:
            recipients = recipients.filter(
                memberships__role__can_edit_partner=True,
                memberships__organization_id=members_organization_id,
            ).exclude(id__in=exclusion)

        can_send_message = with_permissions.get("can_send_message")
        if can_send_message:
            recipients = recipients.filter(
                memberships__role__can_send_message=True,
                memberships__organization_id=members_organization_id,
            ).exclude(id__in=exclusion)
        can_edit_organization = with_permissions.get("can_edit_organization")
        if can_edit_organization:
            recipients = recipients.filter(
                memberships__role__can_edit_organization=True,
                memberships__organization_id=members_organization_id,
            ).exclude(id__in=exclusion)
        can_see_stats = with_permissions.get("can_see_stats")
        if can_see_stats:
            recipients = recipients.filter(
                memberships__role__can_see_stats=True,
                memberships__organization_id=members_organization_id,
            ).exclude(id__in=exclusion)

    for recipient in recipients:
        NotificationService.create_notification(
            recipient=recipient,
            sender=sender,
            mode=mode,
            notification_type=notification_type,
            title=title,
            description=description,
            organization=organization,
            extra_data=extra_data,
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
            extra_data=extra_data,
        )


@shared_task
def send_notifications_to_subscribers(
    sender_id: Union[int, None] = None,
    mode="system",
    notification_type="system",
    title="Title was not sent",
    description="Description was not sent",
    extra_data=None,
    organization_id=None,
):
    sender = sender_id
    if sender_id:
        sender = User.objects.get(id=sender_id)
    recipients = User.objects.filter(subscriptions__organization_id=organization_id)
    organization = Organization.objects.get(id=organization_id)
    for recipient in recipients:
        if not extra_data:
            extra_data = dict()
            can_send_message = user_can_send_message(
                user=recipient, organization_id=organization_id
            )
            extra_data["can_send_message"] = can_send_message

        NotificationService.create_notification(
            recipient=recipient,
            sender=sender,
            mode=mode,
            notification_type=notification_type,
            title=title,
            description=description,
            organization=organization,
            extra_data=extra_data,
        )


@shared_task
def send_notifications_to_deliverers(
    cart_id,
    sender_id: Union[int, None] = None,
    mode=constants.NOTIFICATION_MODE_SYSTEM,
    notification_type=constants.NOTIFICATION_TYPE_AVAILABLE_DELIVERY,
    title="Title was not sent",
    description="Description was not sent",
    extra_data=None,
):
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
        Q(
            memberships__organization__country=country,
            memberships__organization__is_active=True,
            memberships__organization__is_banned=False,
            memberships__organization__is_deleted=False,
            memberships__organization__is_delivery_service=True,
        )
        & Q(
            Q(memberships__role__can_see_stats=True)
            | Q(memberships__role__can_edit_organization=True)
            | Q(memberships__role__can_deliver=True)
        )
    ).distinct()
    extra_data = {
        "organization": organization.title,
        "final_price": str(cart.transaction.final_amount),
        "currency": cart.transaction.currency.code,
        "who_pays": cart.transaction.delivery_info.who_pays,
        "transaction_id": cart.transaction.id,
        "delivery_amount": str(cart.transaction.delivery_info.amount),
        "delivery_currency": str(cart.transaction.delivery_info.currency.code),
        "delivery_organization_id": None,
        "delivery_organization_title": None,
        "delivery_organization": None,
        "delivery_organization_image": None,
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
            extra_data=extra_data,
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
            extra_data=extra_data,
        )


@shared_task
def send_delivery_notitication_to_organization_or_client(
    recipient,
    cart_id,
    notification_type,
    sender_id: Union[int, None] = None,
    mode=constants.NOTIFICATION_MODE_PRODUCT,
    title="Title was not sent",
    description="Description was not sent",
    extra_data=None,
):
    sender = sender_id
    if sender_id:
        sender = User.objects.get(id=sender_id)
    cart = Cart.objects.get(pk=cart_id)
    organization = cart.organization

    delivery_organization = cart.transaction.delivery_info.delivery_organization

    extra_data = {
        "organization": organization.title,
        "delivery_organization_id": delivery_organization.id
        if delivery_organization
        else None,
        "delivery_organization_title": delivery_organization.title
        if delivery_organization
        else None,
        "delivery_organization": delivery_organization.title
        if delivery_organization
        else None,
        "delivery_organization_image": delivery_organization.image.small.url
        if delivery_organization
        else None,
        "final_price": str(cart.transaction.final_amount),
        "original_price": str(cart.transaction.original_amount),
        "currency": cart.transaction.currency.code,
        "who_pays": cart.transaction.delivery_info.who_pays,
        "transaction_id": cart.transaction.id,
        "delivery_amount": str(cart.transaction.delivery_info.amount),
    }
    try:
        extra_data["delivery_currency"] = str(
            cart.transaction.delivery_info.currency.code
        )
    except AttributeError:
        extra_data["delivery_currency"] = str(cart.transaction.currency.code)

    NotificationService.create_notification(
        recipient=recipient,
        sender=sender,
        mode=mode,
        notification_type=notification_type,
        title=title,
        description=description,
        organization=organization,
        extra_data=extra_data,
    )


@shared_task
def send_delivery_notifications(transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    send_delivery_notitication_to_organization_or_client(
        transaction.cart.organization.owner,
        transaction.cart.id,
        NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
        mode=NOTIFICATION_MODE_SYSTEM,
    )

    organization_members = list(
        transaction.cart.organization.memberships.filter(
            Q(role__can_edit_organization=True)
            | Q(role__can_see_stats=True)
            | Q(role__can_deliver=True)
        )
    )
    for member in organization_members:
        send_delivery_notitication_to_organization_or_client(
            member.user,
            transaction.cart.id,
            NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
            mode=NOTIFICATION_MODE_SYSTEM,
        )


@shared_task
def sent_notification(
    recipient_id: int,
    sender_id=None,
    mode="system",
    notification_type="system",
    extra_data=None,
    title="Title was not sent",
    description="Description was not sent",
    organization_id=None,
    item_id=None,
):
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
        extra_data=extra_data,
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


@shared_task
def send_notification(
    cls,
    user: str,
    title: str,
    title_ru: str,
    title_de: str,
    title_tr: str,
    title_zh: str,
    description: str,
    description_ru: str,
    description_de: str,
    description_tr: str,
    description_zh: str,
    notification_id: int,
    mode: str,
    type: str,
    organization=None,
    extra_data=None,
    item=None,
):
    if user:
        user = User.objects.get(id=user)
    organization_image = (
        (
            cls.get_organization_small_image(organization=organization)
            if organization
            else None
        ),
    )
    image = (
        cls.get_item_small_image(item=item)
        if type == "new_comment"
        else organization_image
    )
    if not NotificationSetting.objects.filter(user=user).exists():
        return

    notification_setting = NotificationSetting.objects.get(user=user)

    if not (
        (
            mode == NOTIFICATION_MODE_DISCOUNT
            and notification_setting.discount_notifications
        )
        or (
            mode == NOTIFICATION_MODE_PERSONAL
            and notification_setting.private_notifications
        )
        or (
            mode == NOTIFICATION_MODE_SYSTEM
            and notification_setting.private_notifications
        )
        or (
            mode == NOTIFICATION_MODE_PARTNER
            and notification_setting.organization_notifications
        )
        or (
            mode == NOTIFICATION_MODE_PRODUCT
            and notification_setting.product_notifications
        )
        or (
            mode == NOTIFICATION_MODE_RENTAL
            and notification_setting.rental_notifications
        )
        or (
            mode == NOTIFICATION_MODE_TICKET
            and notification_setting.ticket_notifications
        )
        or (
            mode == NOTIFICATION_MODE_RESUME
            and notification_setting.resume_notifications
        )
    ):
        return

    data = {
        "notification_id": str(notification_id),
        "organization_id": str(organization.id) if organization else "",
        "organization_title": str(organization.title) if organization else "",
        "item_id": str(item.id) if item else "",
        "item_name": str(item.name) if item else "",
        "image": str(image),
        "type": str(type),
        "icon": (
            str(cls.get_organization_small_image(organization=organization))
            if organization
            else ""
        ),
        **{str(k): str(v) for k, v in (extra_data or {}).items()},
    }

    data_en = {
        "title": title,
        "body": description,
        "notification_id": str(notification_id),
        "organization_id": str(organization.id) if organization else "",
        "organization_title": str(organization.title) if organization else "",
        "item_id": str(item.id) if item else "",
        "item_name": str(item.name) if item else "",
        "image": str(image),
        "type": str(type),
        "icon": (
            str(cls.get_organization_small_image(organization=organization))
            if organization
            else ""
        ),
        **{str(k): str(v) for k, v in (extra_data or {}).items()},
    }

    data_ru = {
        "title": title_ru,
        "body": description_ru,
        "notification_id": str(notification_id),
        "organization_id": str(organization.id) if organization else "",
        "organization_title": str(organization.title) if organization else "",
        "item_id": str(item.id) if item else "",
        "item_name": str(item.name) if item else "",
        "image": str(image),
        "type": str(type),
        "icon": (
            str(cls.get_organization_small_image(organization=organization))
            if organization
            else ""
        ),
        **{str(k): str(v) for k, v in (extra_data or {}).items()},
    }

    data_de = {
        "title": title_de,
        "body": description_de,
        "notification_id": str(notification_id),
        "organization_id": str(organization.id) if organization else "",
        "organization_title": str(organization.title) if organization else "",
        "item_id": str(item.id) if item else "",
        "item_name": str(item.name) if item else "",
        "image": str(image),
        "type": str(type),
        "icon": (
            str(cls.get_organization_small_image(organization=organization))
            if organization
            else ""
        ),
        **{str(k): str(v) for k, v in (extra_data or {}).items()},
    }

    data_zh = {
        "title": title_zh,
        "body": description_zh,
        "notification_id": str(notification_id),
        "organization_id": str(organization.id) if organization else "",
        "organization_title": str(organization.title) if organization else "",
        "item_id": str(item.id) if item else "",
        "item_name": str(item.name) if item else "",
        "image": str(image),
        "type": str(type),
        "icon": (
            str(cls.get_organization_small_image(organization=organization))
            if organization
            else ""
        ),
        **{str(k): str(v) for k, v in (extra_data or {}).items()},
    }
    data_tr = {
        "title": title_tr,
        "body": description_tr,
        "notification_id": str(notification_id),
        "organization_id": str(organization.id) if organization else "",
        "organization_title": str(organization.title) if organization else "",
        "item_id": str(item.id) if item else "",
        "item_name": str(item.name) if item else "",
        "image": str(image),
        "type": str(type),
        "icon": (
            str(cls.get_organization_small_image(organization=organization))
            if organization
            else ""
        ),
        **{str(k): str(v) for k, v in (extra_data or {}).items()},
    }

    notification_payload_web = Message(data=data_en)
    notification_payload_web_ru = Message(data=data_ru)
    notification_payload_web_de = Message(data=data_de)
    notification_payload_web_zh = Message(data=data_zh)
    notification_payload_web_tr = Message(data=data_tr)

    from firebase_admin.messaging import Notification

    notification_payload = Message(
        notification=Notification(title=title, body=description, image=str(image)),
        data=data,
    )

    notification_payload_ru = Message(
        notification=Notification(
            title=title_ru, body=description_ru, image=str(image)
        ),
        data=data,
    )

    notification_payload_de = Message(
        notification=Notification(
            title=title_de, body=description_de, image=str(image)
        ),
        data=data,
    )

    notification_payload_zh = Message(
        notification=Notification(
            title=title_zh, body=description_zh, image=str(image)
        ),
        data=data,
    )

    notification_payload_tr = Message(
        notification=Notification(
            title=title_tr, body=description_tr, image=str(image)
        ),
        data=data,
    )

    fcm_devices_ru = notification_setting.fcm_device.filter(
        settingstotoken__language="ru", type="ios"
    )
    fcm_devices_ru.send_message(
        notification_payload_ru, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_en = notification_setting.fcm_device.filter(
        settingstotoken__language="en", type="ios"
    )
    fcm_devices_en.send_message(
        notification_payload, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_de = notification_setting.fcm_device.filter(
        settingstotoken__language="de", type="ios"
    )
    fcm_devices_de.send_message(
        notification_payload_de, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_tr = notification_setting.fcm_device.filter(
        settingstotoken__language="tr", type="ios"
    )
    fcm_devices_tr.send_message(
        notification_payload_tr, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_zh = notification_setting.fcm_device.filter(
        settingstotoken__language="zh", type="ios"
    )
    fcm_devices_zh.send_message(
        notification_payload_zh, dry_run=settings.FCM_DRY_RUN_ENABLE
    )

    fcm_devices_ru_web = notification_setting.fcm_device.filter(
        settingstotoken__language="ru", type="web"
    )
    fcm_devices_ru_web.send_message(
        notification_payload_web_ru, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_en_web = notification_setting.fcm_device.filter(
        settingstotoken__language="en", type="web"
    )
    fcm_devices_en_web.send_message(
        notification_payload_web, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_de_web = notification_setting.fcm_device.filter(
        settingstotoken__language="de", type="web"
    )
    fcm_devices_de_web.send_message(
        notification_payload_web_de, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_tr_web = notification_setting.fcm_device.filter(
        settingstotoken__language="tr", type="web"
    )
    fcm_devices_tr_web.send_message(
        notification_payload_web_tr, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_zh_web = notification_setting.fcm_device.filter(
        settingstotoken__language="zh", type="web"
    )
    fcm_devices_zh_web.send_message(
        notification_payload_web_zh, dry_run=settings.FCM_DRY_RUN_ENABLE
    )

    fcm_devices_ru_android = notification_setting.fcm_device.filter(
        settingstotoken__language="ru", type="android"
    )
    fcm_devices_ru_android.send_message(
        notification_payload_ru, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_en_android = notification_setting.fcm_device.filter(
        settingstotoken__language="en", type="android"
    )
    fcm_devices_en_android.send_message(
        notification_payload, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_de_android = notification_setting.fcm_device.filter(
        settingstotoken__language="de", type="android"
    )
    fcm_devices_de_android.send_message(
        notification_payload_de, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_tr_android = notification_setting.fcm_device.filter(
        settingstotoken__language="tr", type="android"
    )
    fcm_devices_tr_android.send_message(
        notification_payload_tr, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
    fcm_devices_zh_android = notification_setting.fcm_device.filter(
        settingstotoken__language="zh", type="android"
    )
    fcm_devices_zh_android.send_message(
        notification_payload_zh, dry_run=settings.FCM_DRY_RUN_ENABLE
    )
