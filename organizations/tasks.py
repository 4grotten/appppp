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


@shared_task
def parse_instagram_to_shop_items(organization_id: int, posts_count: int = INSTAGRAM_POSTS_TO_PARSE,
                                  anonymous: bool = False):
    video_expired_time = now() + timedelta(days=settings.INSTAGRAM_VIDEO_EXPIRE_DAYS)
    mix_content_expired_time = now() + timedelta(days=settings.INSTAGRAM_IMG_EXPIRE_DAYS)

    organization = Organization.objects.get(id=organization_id)
    instagram_integration = InstagramIntegration.objects.get(organization=organization)
    instagram_posts = parser.get_posts(instagram_integration.account_user_id, posts_count=posts_count, anonymous=anonymous)
    for instagram in instagram_posts:
        if not ShopItem.objects.filter(
                created_at=instagram.get('created_at'),
                organization=organization):
            description = instagram.pop('description')
            created_at = instagram.pop('created_at')
            post_url = instagram.pop('post_url')
            shop_item = ShopItem.objects.create(name="Instagram", organization=organization, created_at=created_at,
                                                updated_at=created_at, description=description, instagram_link=post_url,
                                                )
            for data in instagram.get('data'):
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
                ItemInstagramData.objects.create(item=shop_item,
                                                 thumbnail_url=data.get('thumbnail_url'),
                                                 video_url=data.get('video_url'))

            if ShopItem.objects.filter(id=shop_item.id, instagram_data__video_url=None):
                shop_item.removed_at = mix_content_expired_time
                shop_item.save()
            else:
                shop_item.removed_at = video_expired_time
                shop_item.save()


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

