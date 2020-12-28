from django.db.models import F
from instagram_parsers.parsers import parser
from shop.models import ShopItem, ItemInstagramData
from celery import shared_task
from organizations.models import Organization, InstagramIntegration


@shared_task
def update_instagram_videos(organization_id: int):
    pass
