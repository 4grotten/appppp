from instagram_parsers.parsers.parser import get_video_url_from_post
from shop.models import ItemInstagramData
from celery import shared_task


@shared_task
def update_instagram_videos():
    instagram_data = ItemInstagramData.objects.filter(video_url__isnull=False)
    for data in instagram_data:
        video_url = get_video_url_from_post(data.post_pk)
        data.video_ur = video_url
        data.save()
