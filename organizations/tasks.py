from datetime import date, timedelta, datetime
from django.utils import timezone
from instagram_parser import parser
# from instagram_parser.get_id import get_username_from_instagram_url, usernametoid
from shop.models import ShopItem
from celery import shared_task
from organizations.models import Organization


@shared_task
def parse_instagram_to_shop_items(organization_id: int, url: str):
    organization = Organization.objects.get(id=organization_id)
    instagram_posts = parser.get_posts(123123132)
    for instagram in instagram_posts:
        if not ShopItem.objects.filter(
                created_at=timezone.make_aware(datetime.utcfromtimestamp(instagram.get('created_at'))),
                organization=organization):
            description = instagram.get('description')
            instagram.pop('description')
            created_at = timezone.make_aware(datetime.utcfromtimestamp(instagram.get('created_at')), )
            instagram.pop('created_at')
            ShopItem.objects.create(name="Instagram", organization=organization, created_at=created_at,
                                    updated_at=created_at, instagram_data=instagram, description=description)
