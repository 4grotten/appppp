from datetime import date, timedelta, datetime
from django.utils import timezone
from instagram_parser import get_id, parser
from shop.models import ShopItem
from celery import shared_task
from organizations.models import Organization


@shared_task
def parse_instagram_to_shop_items(organization_id: int, url: str, instagram_id: int = 248150720):
    organization = Organization.objects.get(id=organization_id)
    instagram_posts = parser.get_posts(instagram_id)
    for instagram in instagram_posts:
        if not ShopItem.objects.filter(
                created_at=timezone.make_aware(datetime.utcfromtimestamp(instagram.get('created_at')), )):
            shop_item = ShopItem.objects.create(name="Instagram", organization=organization)
            shop_item.description = instagram.get('description')
            instagram.pop('description')
            shop_item.created_at = timezone.make_aware(datetime.utcfromtimestamp(instagram.get('created_at')), )
            instagram.pop('created_at')
            shop_item.instagram_data = instagram
            shop_item.save()
