from datetime import date, timedelta, datetime
from django.utils import timezone
from instagram_parser import get_id, parser
from shop.models import ShopItem
from celery import shared_task
from organizations.models import Organization


@shared_task
def parse_instagram_to_shop_items(organization_id: int, url: str):
    organization = Organization.objects.get(id=organization_id)
    # username = get_id.get_username_from_instagram_url(url=url)
    # user_id = get_id.usernametoid(username)
    instagram_posts = parser.get_posts(304803426)
    for instagram in instagram_posts:
        if not ShopItem.objects.filter(
                created_at=timezone.make_aware(datetime.utcfromtimestamp(instagram.get('created_at')), )):
            shop_item = ShopItem.objects.create(name="Instagram", organization=organization)
            shop_item.created_at = timezone.make_aware(datetime.utcfromtimestamp(instagram.get('created_at')), )
            instagram.pop('created_at')
            shop_item.instagram_data = instagram
            shop_item.save()
