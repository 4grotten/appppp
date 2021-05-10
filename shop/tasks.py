from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils.timezone import now

from instagram_parsers.parsers.parser import get_video_url_from_post
from shop.models import ItemInstagramData, ShopItem


@shared_task
def update_instagram_videos():
    update_posts_before = now() - timedelta(days=settings.INSTAGRAM_VIDEO_EXPIRE_DAYS)
    data_with_video = ItemInstagramData.objects.filter(
        updated_at__lte=update_posts_before, video_url__isnull=False
    ).order_by('updated_at')[:settings.INSTAGRAM_POSTS_UPDATE_BATCH_SIZE]
    for data in data_with_video:
        video_url = get_video_url_from_post(post_url=data.item.instagram_link)
        data.video_url = video_url
        data.save()


@shared_task
def delete_old_instagram_posts():
    delete_until = now() - timedelta(days=settings.INSTAGRAM_DAYS_TO_KEEP)
    ShopItem.objects.filter(updated_at__lte=delete_until, instagram_data__isnull=False).delete()
