import logging
import time
import random

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db import transaction
from django.db.models import Subquery
from django.utils.timezone import now
from instagram_parsers.models import LoginDevice
from instagram_parsers.parsers import parser
from notifications.constants import NEW_COMMENT_TYPE
from notifications.models import Notification
from organizations.constants import INSTAGRAM_POSTS_TO_PARSE
from organizations.models import InstagramIntegration, Organization
from shop.models import ShopItem, ItemInstagramData
from users.models import User

logger = logging.getLogger(__name__)
@shared_task
def parse_instagram_to_shop_items(organization_id: int, posts_count: int = INSTAGRAM_POSTS_TO_PARSE,
                                  anonymous: bool = False):
    logger.info(
        f"Starting Instagram parsing for organization_id={organization_id}, posts_count={posts_count}, anonymous={anonymous}")

    video_expired_time = now() + timedelta(days=settings.INSTAGRAM_VIDEO_EXPIRE_DAYS)
    mix_content_expired_time = now() + timedelta(days=settings.INSTAGRAM_IMG_EXPIRE_DAYS)

    try:
        organization = Organization.objects.get(id=organization_id)
        logger.info(f"Found organization: {organization}")
    except Organization.DoesNotExist:
        logger.error(f"Organization with id={organization_id} does not exist.")
        return

    try:
        instagram_integration = InstagramIntegration.objects.get(organization=organization)
        logger.info(f"Found Instagram integration for organization: {instagram_integration}")
    except InstagramIntegration.DoesNotExist:
        logger.error(f"Instagram integration for organization id={organization_id} not found.")
        return

    try:
        instagram_posts = parser.get_posts(instagram_integration.account_user_id, posts_count=posts_count,
                                           anonymous=anonymous)
        logger.info(f"Fetched {len(instagram_posts)} posts from Instagram.")
    except Exception as e:
        logger.exception("Failed to fetch posts from Instagram.")
        return

    for index, instagram in enumerate(instagram_posts):
        logger.debug(f"Processing post #{index + 1}: {instagram}")
        try:
            if not ShopItem.objects.filter(created_at=instagram.get('created_at'), organization=organization).exists():
                description = instagram.pop('description')
                created_at = instagram.pop('created_at')
                post_url = instagram.pop('post_url')

                shop_item = ShopItem.objects.create(
                    name="Instagram",
                    organization=organization,
                    created_at=created_at,
                    updated_at=created_at,
                    description=description,
                    instagram_link=post_url,
                )
                logger.info(f"Created ShopItem id={shop_item.id} for post_url={post_url}")

                for data in instagram.get('data', []):
                    ItemInstagramData.objects.create(
                        item=shop_item,
                        thumbnail_url=data.get('thumbnail_url'),
                        video_url=data.get('video_url')
                    )
                    logger.debug(f"Added ItemInstagramData for ShopItem id={shop_item.id}: {data}")

                if ShopItem.objects.filter(id=shop_item.id, instagram_data__video_url=None).exists():
                    shop_item.removed_at = mix_content_expired_time
                    logger.debug(f"Set removed_at (IMG) for ShopItem id={shop_item.id}")
                else:
                    shop_item.removed_at = video_expired_time
                    logger.debug(f"Set removed_at (VIDEO) for ShopItem id={shop_item.id}")

                shop_item.save()
        except Exception as e:
            logger.exception(f"Error processing Instagram post: {instagram}")

    logger.info(f"Completed parsing Instagram posts for organization_id={organization_id}")


@shared_task
def delete_not_updated_posts_from_instagram(organization_id: int):
    ShopItem.objects.filter(organization_id=organization_id, name='Instagram', price=None,
                            is_updated=False, removed_at__isnull=False).delete()


@shared_task
def delete_old_instagram_posts():
    delete_until = now() - timedelta(days=settings.INSTAGRAM_DAYS_TO_KEEP)
    qs = ShopItem.objects.filter(name='Instagram', instagram_data__isnull=False,
                                 instagram_data__updated_at__lte=delete_until)
    transaction.on_commit(
        lambda: Notification.objects.filter(
            item__in=qs,
            type__in=[NEW_COMMENT_TYPE, ]
        ).delete())
    qs.delete()


@shared_task
def delete_expired_photo_and_posts():
    from shop.services.item_services import ShopItemService
    ItemInstagramData.objects.filter(item__removed_at__lte=now()).delete()
    ShopItemService.delete_expired_posts()


@shared_task
def delete_expired_video_url():
    delete_until = now() - timedelta(days=settings.INSTAGRAM_VIDEO_EXPIRE_DAYS)
    shop_item = ShopItem.objects.filter(instagram_data__updated_at__lte=delete_until,
                                        instagram_data__video_url__isnull=False, removed_at__isnull=False)
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
    ).order_by('updated_at')[:settings.INSTAGRAM_POSTS_UPDATE_BATCH_SIZE]
    for data in data_with_video:
        video_url, thumbnail_url = parser.get_video_urls_from_post(post_url=data.item.instagram_link)
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

    items = ShopItem.objects.filter(organization=organization_id,
                                    instagram_data__updated_at__lte=update_posts_before_this_date,
                                    instagram_data__video_url__isnull=without_video).order_by('-updated_at')

    for item in items:
        post_data = parser.get_urls_from_post(post_url=item.instagram_link)
        item.instagram_data.all().delete()
        for data in post_data:
            ItemInstagramData.objects.create(item=item,
                                             thumbnail_url=data.get('thumbnail_url'),
                                             video_url=data.get('video_url'))


@shared_task
def update_login_device_settings():
    expiration_time = settings.INSTAGRAM_LOGIN_DEVICE_EXPIRE_DAYS
    update_login_device_before_this_date = now() - timedelta(days=expiration_time)
    devices = LoginDevice.objects.filter(updated_at__lte=update_login_device_before_this_date)
    if devices:
        for device in devices:
            proxy = f'http://{device.proxy_login}:{device.proxy_password}@{device.proxy_http_s}'
            device.settings = parser.get_settings_login_device(device.username, device.password, proxy=proxy)
            device.save()


@shared_task
def add_subscribers_to_organization(organization_id, num_members):
    from organizations.services.subscription_services import SubscriptionService
    from organizations.services.organization_services import OrganizationService

    users = User.objects.filter(is_active=True, full_name__isnull=False, avatar__isnull=False) \
        .exclude(id=Subquery(Organization.objects.filter(id=organization_id).values('owner_id'))) \
        .exclude(phone_number__icontains='+996')
    if users.count() < num_members:
        num_members = users.count()
    random_users = random.sample(list(users), num_members)

    organization = OrganizationService.get(pk=organization_id)

    for subscription in random_users:
        time.sleep(random.randint(60, 3600))
        SubscriptionService.toggle_subscription_status(
            organization=organization, user=subscription
        )

