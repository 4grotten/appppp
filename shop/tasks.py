from celery import shared_task

from instagram_parsers.parsers.parser import get_video_url_from_post
from shop.models import ItemInstagramData, ItemSubcategory


@shared_task
def update_instagram_videos():
    instagram_data = ItemInstagramData.objects.filter(video_url__isnull=False)
    for data in instagram_data:
        video_url = get_video_url_from_post(data.post_pk)
        data.video_url = video_url
        data.save()


@shared_task
def upload_item_subcategories(csv_data, category_id):
    splited_data = csv_data.splitlines()
    for line in splited_data:
        (category_ru, category_en, category_tr) = line.split(";")
        _, _ = ItemSubcategory.objects.update_or_create(
            category_id=category_id,
            name_ru=category_ru,
            name_en=category_en,
            name_tr=category_tr
        )
