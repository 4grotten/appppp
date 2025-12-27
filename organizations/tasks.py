import json
import logging
import random
import time
from datetime import datetime, timedelta
from decimal import Decimal
from itertools import groupby
from zoneinfo import ZoneInfo

import requests
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Subquery
from django.template.loader import render_to_string
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from weasyprint import HTML

from common.services.slack import bot
from instagram_parsers.models import LoginDevice
from instagram_parsers.parsers import parser
from notifications.constants import NEW_COMMENT_TYPE
from notifications.models import Notification
from organizations.constants import INSTAGRAM_POSTS_TO_PARSE
from organizations.models import (
    Assistant,
    Coupon,
    InstagramIntegration,
    Invoice,
    Organization,
    OrganizationInvoiceInfo,
    RegionalTariff,
    UserOrgSubscription,
)
from organizations.services.invoice_service import OrganizationInvoiceService
from organizations.utils import clean_original_amount
from shop.models import ItemInstagramData, ShopItem
from users.models import User

logger = logging.getLogger(__name__)


@shared_task
def parse_instagram_to_shop_items(
    organization_id: int,
    posts_count: int = INSTAGRAM_POSTS_TO_PARSE,
    anonymous: bool = False,
):
    video_expired_time = now() + timedelta(days=settings.INSTAGRAM_VIDEO_EXPIRE_DAYS)
    mix_content_expired_time = now() + timedelta(
        days=settings.INSTAGRAM_IMG_EXPIRE_DAYS
    )

    organization = Organization.objects.get(id=organization_id)
    instagram_integration = InstagramIntegration.objects.get(organization=organization)
    instagram_posts = parser.get_posts(
        instagram_integration.account_user_id,
        posts_count=posts_count,
        anonymous=anonymous,
    )
    for instagram in instagram_posts:
        post_date = instagram.get("created_at")

        if isinstance(post_date, (int, float)):
            post_date = datetime.fromtimestamp(post_date)

        elif isinstance(post_date, str):
            post_date = parse_datetime(post_date)

        if not post_date:
            post_date = datetime.now()

        if not ShopItem.objects.filter(created_at=post_date, organization=organization):
            description = instagram.pop("description")
            post_url = instagram.pop("post_url")
            shop_item = ShopItem.objects.create(
                name="Instagram",
                organization=organization,
                created_at=post_date,
                updated_at=post_date,
                description=description,
                instagram_link=post_url,
            )
            for data in instagram.get("data"):
                # if data.get('video_url'):
                #     thumbnail = File.objects.create(image_url=data.get('thumbnail_url'))
                #     video = FileVideo.objects.create(video_url=data.get('video_url'),
                #                                      thumbnail=thumbnail)
                #     ItemInstagramData.objects.create(item=shop_item,
                #                                      thumbnail_url='https://apofiz-media.s3.eu-central-1.amazonaws.com/' + str(
                #                                          thumbnail),
                #                                      video_url='https://apofiz-media.s3.eu-central-1.amazonaws.com/' + str(
                #                                          video))
                # else:
                ItemInstagramData.objects.create(
                    item=shop_item,
                    thumbnail_url=data.get("thumbnail_url"),
                    video_url=data.get("video_url"),
                )

            if ShopItem.objects.filter(id=shop_item.id, instagram_data__video_url=None):
                shop_item.removed_at = mix_content_expired_time
                shop_item.save()
            else:
                shop_item.removed_at = video_expired_time
                shop_item.save()


@shared_task
def delete_not_updated_posts_from_instagram(organization_id: int):
    ShopItem.objects.filter(
        organization_id=organization_id,
        name="Instagram",
        price=None,
        is_updated=False,
        removed_at__isnull=False,
    ).delete()


@shared_task
def delete_old_instagram_posts():
    delete_until = now() - timedelta(days=settings.INSTAGRAM_DAYS_TO_KEEP)
    qs = ShopItem.objects.filter(
        name="Instagram",
        instagram_data__isnull=False,
        instagram_data__updated_at__lte=delete_until,
    )
    transaction.on_commit(
        lambda: Notification.objects.filter(
            item__in=qs,
            type__in=[
                NEW_COMMENT_TYPE,
            ],
        ).delete()
    )
    qs.delete()


@shared_task
def delete_expired_photo_and_posts():
    from shop.services.item_services import ShopItemService

    ItemInstagramData.objects.filter(item__removed_at__lte=now()).delete()
    ShopItemService.delete_expired_posts()


@shared_task
def delete_expired_video_url():
    delete_until = now() - timedelta(days=settings.INSTAGRAM_VIDEO_EXPIRE_DAYS)
    shop_item = ShopItem.objects.filter(
        instagram_data__updated_at__lte=delete_until,
        instagram_data__video_url__isnull=False,
        removed_at__isnull=False,
    )
    for item in shop_item:
        if item.instagram_data.filter(video_url=None):
            insta_data_list = item.instagram_data.filter(video_url__isnull=False)
            for insta_data in insta_data_list:
                insta_data.video_url = None
                insta_data.save()
        else:
            insta_data_list = item.instagram_data.all()
            for insta_data in insta_data_list:
                insta_data.video_url = None
                item.removed_at = item.removed_at + timedelta(days=2)
                item.save()
                insta_data.save()


@shared_task
def update_instagram_videos():
    update_posts_before = now() - timedelta(days=settings.INSTAGRAM_VIDEO_EXPIRE_DAYS)
    data_with_video = ItemInstagramData.objects.filter(
        updated_at__lte=update_posts_before, video_url__isnull=False
    ).order_by("updated_at")[: settings.INSTAGRAM_POSTS_UPDATE_BATCH_SIZE]
    for data in data_with_video:
        video_url, thumbnail_url = parser.get_video_urls_from_post(
            post_url=data.item.instagram_link
        )
        data.video_url = video_url
        if thumbnail_url is not None:
            data.thumbnail_url = thumbnail_url
        data.save()


@shared_task
def update_media_url_by_user_entering_on_page(organization_id, without_video=False):
    if not without_video:
        expiration_time = settings.INSTAGRAM_VIDEO_EXPIRE_DAYS
    else:
        expiration_time = settings.INSTAGRAM_IMG_EXPIRE_DAYS
    update_posts_before_this_date = now() - timedelta(days=expiration_time)

    items = ShopItem.objects.filter(
        organization=organization_id,
        instagram_data__updated_at__lte=update_posts_before_this_date,
        instagram_data__video_url__isnull=without_video,
    ).order_by("-updated_at")

    for item in items:
        post_data = parser.get_urls_from_post(post_url=item.instagram_link)
        item.instagram_data.all().delete()
        for data in post_data:
            ItemInstagramData.objects.create(
                item=item,
                thumbnail_url=data.get("thumbnail_url"),
                video_url=data.get("video_url"),
            )


@shared_task
def update_login_device_settings():
    expiration_time = settings.INSTAGRAM_LOGIN_DEVICE_EXPIRE_DAYS
    update_login_device_before_this_date = now() - timedelta(days=expiration_time)
    devices = LoginDevice.objects.filter(
        updated_at__lte=update_login_device_before_this_date
    )
    if devices:
        for device in devices:
            proxy = f"http://{device.proxy_login}:{device.proxy_password}@{device.proxy_http_s}"
            device.settings = parser.get_settings_login_device(
                device.username, device.password, proxy=proxy
            )
            device.save()


@shared_task
def subscribe_user_to_organization(organization_id, user_id):
    from organizations.services.organization_services import OrganizationService
    from organizations.services.subscription_services import SubscriptionService
    from users.models import User

    organization = OrganizationService.get(pk=organization_id)
    user = User.objects.get(pk=user_id)

    # 1 minute and 15 minutes
    time.sleep(random.randint(60, 900))

    SubscriptionService.toggle_subscription_status(organization=organization, user=user)


@shared_task
def add_subscribers_to_organization(organization_id, num_members):
    users = (
        User.objects.filter(
            is_active=True, full_name__isnull=False, avatar__isnull=False
        )
        .exclude(
            id=Subquery(
                Organization.objects.filter(id=organization_id).values("owner_id")
            )
        )
        .exclude(phone_number__icontains="+996")
    )
    if users.count() < num_members:
        num_members = users.count()
    selected_users = random.sample(list(users), num_members)

    for user in selected_users:
        subscribe_user_to_organization.delay(organization_id, user.id)


@shared_task
def process_comment_with_assistant(
    item_info, organization_info, comment_id, assistant_id
):
    from shop.models import Comment
    from shop.services.comment_services import CommentService

    comment = Comment.objects.get(id=comment_id)
    assistant = Assistant.objects.get(id=assistant_id)

    try:
        response = requests.post(
            "http://161.35.153.151:8080/bot/comments/",
            json={
                "question": comment.text,
                "training_data": {
                    "assistant_info": {
                        "organization": assistant.organization.title,
                        "name": assistant.name,
                        "gender": assistant.gender,
                        "position": assistant.position,
                        "is_enabled": assistant.is_enabled,
                    },
                    "item_info": item_info,
                    "organization_info": organization_info,
                },
            },
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        return {"error": str(e)}

    item = ShopItem.objects.get(id=item_info["id"])

    return CommentService.create_assistant_comment(
        text=result["answer"], item=item, parent=comment, assistant=assistant
    )


@shared_task
def expire_coupons():
    coupons = Coupon.objects.filter(is_active=True, is_updating=False).select_related(
        "product__organization__city"
    )

    coupons = sorted(coupons, key=lambda c: c.product.organization.city.timezone)
    to_expire_ids = []

    for tz_name, group in groupby(
        coupons, key=lambda c: c.product.organization.city.timezone
    ):
        tz = ZoneInfo(tz_name)
        now_local = datetime.now(tz)
        expired_ids = [c.id for c in group if c.expire_date.astimezone(tz) < now_local]

        to_expire_ids.extend(expired_ids)

    if to_expire_ids:
        Coupon.objects.filter(id__in=to_expire_ids).update(is_active=False)


@shared_task
def update_posts():
    organizations_ids = Organization.objects.filter(update_posts=True).values(
        "id", "title"
    )
    total_updated = 0
    updated_posts = dict()

    for org_id in organizations_ids:
        items = ShopItem.objects.filter(organization__id=org_id.get("id")).order_by(
            "?"
        )[:10]

        if not items:
            continue
        count = 0
        # items_ids = [item.pk for item in items]
        for item in items:
            item.is_updated = True
            item.updated_at = datetime.now()
            time.sleep(1)
            count += 1

        updated_posts[org_id.get("title", None)] = [item.name for item in items]
        total_updated += count

    msg = f"updated posts with organizations\n\n```{json.dumps(updated_posts, ensure_ascii=False, indent=2)}```"
    bot(msg)

    logger.info(f"Total_updated {total_updated} random shop items")


@shared_task
def create_invoice_pdf(invoice_number: str = None, context: dict = {}):
    if not invoice_number:
        country_data = context.get("country_data")
        code = country_data["code"]
        amount = clean_original_amount(str(country_data["amount"]))
        tax = clean_original_amount(str(country_data.get("tax_amount", 0)))
        payment_method = context.get("payment_method")
        subscription = UserOrgSubscription.objects.get(id=context["subscription_id"])
        org_info = OrganizationInvoiceInfo.objects.get(**context["data"])
        tariff = RegionalTariff.objects.get(id=country_data["tariff_id"])
        invoice_qs = Invoice.objects.create(
            code=code,
            invoice_amount=Decimal(amount),
            invoice_tax=Decimal(tax),
            payment_method=payment_method,
            organization_info=org_info,
            tariff=tariff,
            subscription=subscription,
        )

        invoice_number = invoice_qs.invoice_number
    context["invoice_number"] = invoice_number
    html = render_to_string("invoice.html", context=context)
    pdf_bytes = HTML(string=html).write_pdf()

    file_name = f"{invoice_number}.pdf"
    invoice = Invoice.objects.get(invoice_number=invoice_number)
    if context.get("title") == "invoice":
        invoice.invoice_pdf.save(file_name, ContentFile(pdf_bytes), save=True)
        OrganizationInvoiceService.send_to_email(invoice.pk, "invoice")
    else:
        file_name = f"receipt_{file_name}"
        invoice.receipt_pdf.save(file_name, ContentFile(pdf_bytes), save=True)
        OrganizationInvoiceService.send_to_email(invoice.pk, "receipt")


@shared_task(bind=True, max_retries=30, default_retry_delay=60)
def fetch_maalypay_status(self, merchant_tx_id: str, api_key: str, transaction_id: int):
    # Импорты делаем внутри функции, чтобы избежать циклической зависимости (Circular Import),
    # так как services и models часто ссылаются на tasks.

    import logging
    import requests
    from django.db import transaction
    from django.db.models import Q

    logger = logging.getLogger(__name__)

    logger.info(
        "[MaalyPay Task] Starting status check",
        extra={
            "merchant_tx_id": merchant_tx_id,
            "transaction_id": transaction_id,
            "retry_count": self.request.retries,
        }
    )

    from notifications.constants import (
        ACCEPT_ORDER_PAYMENT_CLIENT_TYPE,
        ACCEPT_ORDER_PAYMENT_TYPE,
        ACCEPT_ORDER_TYPE,
        ACCEPTED_ONLINE_ORDER_CLIENT_TYPE,
        NOTIFICATION_MODE_PRODUCT,
        NOTIFICATION_MODE_SYSTEM,
        NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
    )
    from notifications.models import Notification
    from notifications.tasks import (
        send_delivery_notitication_to_organization_or_client,
        sent_notification,
    )
    from organizations.models import Organization
    from transactions.models import Transaction

    url = f"https://maalyportal.com/api/omerch/check-online-transaction-merch/{merchant_tx_id}"
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response_data = response.json()
        status_value = response_data.get("status")
    except Exception as e:
        print(f"MaalyPay connection error: {e}")
        raise self.retry()

    # Universal status handling: supports both boolean and string formats
    # String pending statuses (legacy format)
    pending_statuses = ["not initiated by customer yet", "pending", "in_progress"]

    # Determine if payment is confirmed based on type
    is_paid = False
    should_retry = False

    if isinstance(status_value, bool):
        # Boolean format: True = paid, False = not paid yet
        is_paid = status_value
        should_retry = not status_value
    elif isinstance(status_value, str):
        # String format: check against pending statuses
        status_lower = status_value.lower()
        if status_lower in pending_statuses:
            should_retry = True
        elif status_lower in ["completed", "success", "paid", "confirmed"]:
            is_paid = True
        else:
            # Unknown status string, treat as not paid and retry
            print(f"MaalyPay: Unknown status string '{status_value}', retrying...")
            should_retry = True
    else:
        # None or unexpected type - retry
        print(f"MaalyPay: Invalid status type {type(status_value)}, retrying...")
        raise self.retry()

    if should_retry:
        print(f"MaalyPay: Transaction {merchant_tx_id} not paid yet (status: {status_value}), retrying...")
        raise self.retry()

    if is_paid:
        try:
            with transaction.atomic():
                old_transaction = Transaction.objects.select_for_update().get(
                    id=transaction_id
                )

                if old_transaction.is_processed:
                    return "Already processed"

                # Collect payment external data before saving
                payment_external_data = {}
                if response_data.get("txHash"):
                    payment_external_data["txHash"] = response_data.get("txHash")
                if response_data.get("network"):
                    payment_external_data["network"] = response_data.get("network")
                if response_data.get("asset"):
                    payment_external_data["asset"] = response_data.get("asset")
                if response_data.get("txLink"):
                    payment_external_data["txLink"] = response_data.get("txLink")

                old_transaction.payment_status = Transaction.ACCEPTED
                old_transaction.is_processed = True
                old_transaction.payment_info = payment_external_data if payment_external_data else None
                old_transaction.save()

                if payment_external_data:
                    print(f"MaalyPay: Stored blockchain data (txHash: {payment_external_data.get('txHash', 'N/A')[:10]}...) for transaction {transaction_id}")

                if old_transaction.type == Transaction.ONLINE:
                    transaction.on_commit(
                        lambda: Notification.objects.filter(
                            Q(extra_data__transaction_id=old_transaction.id)
                            & (
                                Q(type=ACCEPT_ORDER_TYPE)
                                | Q(type=ACCEPTED_ONLINE_ORDER_CLIENT_TYPE)
                            )
                        ).delete()
                    )

                discount_percent = old_transaction.discount_percent

                sent_notification.delay(
                    recipient_id=old_transaction.processed_by_id,
                    sender_id=old_transaction.client_id,
                    mode=NOTIFICATION_MODE_PRODUCT,
                    notification_type=ACCEPT_ORDER_PAYMENT_TYPE,
                    organization_id=old_transaction.organization_id,
                    extra_data=dict(
                        transaction_id=old_transaction.id,
                        total_price=str(old_transaction.final_amount),
                        discount_percent=discount_percent,
                        currency=old_transaction.currency.code,
                    ),
                )

                sent_notification.delay(
                    recipient_id=old_transaction.client_id,
                    sender_id=old_transaction.processed_by_id,
                    mode=NOTIFICATION_MODE_PRODUCT,
                    notification_type=ACCEPT_ORDER_PAYMENT_CLIENT_TYPE,
                    organization_id=old_transaction.organization_id,
                    extra_data=dict(
                        transaction_id=old_transaction.id,
                        total_price=str(old_transaction.final_amount),
                        discount_percent=discount_percent,
                        currency=old_transaction.currency.code,
                    ),
                )

                organization = old_transaction.organization
                has_delivery_service = (
                    Organization.objects.exclude(Q(is_banned=True) | Q(is_deleted=True))
                    .filter(is_delivery_service=True, country=organization.country)
                    .exists()
                )

                if (
                    has_delivery_service
                    and hasattr(old_transaction, "cart")
                    and old_transaction.cart
                ):
                    try:
                        send_delivery_notitication_to_organization_or_client(
                            old_transaction.cart.organization.owner,
                            old_transaction.cart.id,
                            NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                            mode=NOTIFICATION_MODE_SYSTEM,
                        )

                        organization_members = list(
                            old_transaction.cart.organization.memberships.filter(
                                Q(role__can_edit_organization=True)
                                | Q(role__can_see_stats=True)
                                | Q(role__can_deliver=True)
                            )
                        )
                        for member in organization_members:
                            send_delivery_notitication_to_organization_or_client(
                                member.user,
                                old_transaction.cart.id,
                                NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                                mode=NOTIFICATION_MODE_SYSTEM,
                            )
                    except Exception as e:
                        print(f"Error sending delivery notifications: {e}")

                # Generate receipt if this is an org_subscription transaction
                if old_transaction.type == Transaction.ORG_SUBSCRIPTION:
                    try:
                        from organizations.services.receipts_services import ReceiptService

                        org_subscription = old_transaction.org_subscription
                        if org_subscription:
                            ReceiptService.create_receipt_from_maalypay(org_subscription)
                            print(f"MaalyPay: Receipt generated for subscription {org_subscription.pk}")
                    except Exception as e:
                        print(f"MaalyPay: Error generating receipt: {e}")
                        # Don't fail the whole transaction if receipt fails

            return f"Transaction {transaction_id} completed successfully via MaalyPay"

        except Transaction.DoesNotExist:
            print(f"Transaction {transaction_id} not found")
            return "Transaction not found"
        except Exception as e:
            print(f"Error processing MaalyPay transaction db update: {e}")
            raise self.retry()

    # If we reach here, payment was not confirmed
    print(f"MaalyPay: Transaction {merchant_tx_id} payment not confirmed (status: {status_value})")
    return f"Payment not confirmed: {status_value}"
