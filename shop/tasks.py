from celery import shared_task

from instagram_parsers.parsers.parser import get_video_url_from_post
from shop.models import ItemInstagramData


@shared_task
def update_instagram_videos():
    instagram_data = ItemInstagramData.objects.filter(video_url__isnull=False)
    for data in instagram_data:
        video_url = get_video_url_from_post(post_url=data.item.instagram_link)
        data.video_url = video_url
        data.save()
