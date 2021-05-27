from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.db.models import F
from django.utils.timezone import now

from common.exceptions import BadRequestException
from common.models import File
from instagram_parsers.parsers import parser
from instagram_parsers.parsers.get_id import get_username_from_instagram_url
from instagram_parsers.parsers.user_info import get_instagram_user_info
from organizations.constants import INSTAGRAM_POSTS_TO_PARSE
from organizations.models import InstagramIntegration, Organization
from shop.models import ShopItem, ItemInstagramData


@shared_task
def create_instagram_integration(organization_id: int, insta_url: str):
    try:
        organization = Organization.objects.get(id=organization_id)
        username = get_username_from_instagram_url(insta_url)
        user_info = get_instagram_user_info(username)

        avatar = File.objects.create(image_url=user_info.get('profile_image'))
        instance = InstagramIntegration.objects.create(organization=organization,
                                                       url=insta_url,
                                                       account_user_name=username,
                                                       account_user_id=user_info.pop('user_id'),
                                                       account_full_name=user_info.get('full_name'),
                                                       avatar=avatar)

        parse_instagram_to_shop_items.delay(organization_id=organization.id)
        return instance
    except Exception as e:
        raise BadRequestException('Instagram user not found : {e}'.format(e=str(e)))


@shared_task
def parse_instagram_to_shop_items(organization_id: int, posts_count: int = INSTAGRAM_POSTS_TO_PARSE):
    organization = Organization.objects.get(id=organization_id)
    instagram_integration = InstagramIntegration.objects.get(organization=organization)
    instagram_posts = parser.get_posts(instagram_integration.account_user_id, posts_count=posts_count)
    for instagram in instagram_posts:
        if not ShopItem.objects.filter(
                created_at=instagram.get('created_at'),
                organization=organization):
            description = instagram.pop('description')
            created_at = instagram.pop('created_at')
            post_url = instagram.pop('post_url')
            shop_item = ShopItem.objects.create(name="Instagram", organization=organization, created_at=created_at,
                                                updated_at=created_at, description=description, instagram_link=post_url)
            for data in instagram.get('data'):
                ItemInstagramData.objects.create(item=shop_item,
                                                 thumbnail_url=data.get('thumbnail_url'),
                                                 video_url=data.get('video_url'))


@shared_task
def delete_not_updated_posts_from_instagram(organization_id: int):
    ShopItem.objects.filter(organization_id=organization_id, name='Instagram', updated_at=F('created_at')).delete()


@shared_task
def delete_old_instagram_posts():
    delete_until = now() - timedelta(days=settings.INSTAGRAM_DAYS_TO_KEEP)
    ShopItem.objects.filter(name='Instagram', instagram_data__isnull=False,
                            instagram_data__updated_at__lte=delete_until).delete()


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
