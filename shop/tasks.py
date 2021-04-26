from datetime import timedelta

from celery import shared_task
from django.utils.timezone import now

from instagram_parsers.parsers.parser import get_video_url_from_post
from shop.models import ItemInstagramData, ShopItem


@shared_task
def update_instagram_videos():
    instagram_data = ItemInstagramData.objects.filter(video_url__isnull=False)
    for data in instagram_data:
        video_url = get_video_url_from_post(post_url=data.item.instagram_link)
        data.video_url = video_url
        data.save()


@shared_task
def delete_old_instagram_posts():
    days_to_keep = 14
    delete_until = now() - timedelta(days=days_to_keep)
    ShopItem.objects.filter(created_at__lte=delete_until, instagram_data__isnull=False).delete()
