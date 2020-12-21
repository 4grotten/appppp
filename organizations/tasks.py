from datetime import date, timedelta, datetime
from django.utils import timezone
from django.db.models import F
from instagram_parser import parser
from instagram_parser.get_id import get_username_from_instagram_url, usernametoid
from shop.models import ShopItem
from celery import shared_task
from organizations.models import Organization


@shared_task
def parse_instagram_to_shop_items(organization_id: int, url: str):
    organization = Organization.objects.get(id=organization_id)
    username = get_username_from_instagram_url(url)
    user_id = usernametoid(username)
    instagram_posts = parser.get_posts(user_id)
    for instagram in instagram_posts:
        if not ShopItem.objects.filter(
                created_at=instagram.get('created_at'),
                organization=organization):
            description = instagram.get('description')
            instagram.pop('description')
            created_at = instagram.get('created_at')
            instagram.pop('created_at')
            post_url = instagram.get('post_url')
            instagram.pop('post_url')
            ShopItem.objects.create(name="Instagram", organization=organization, created_at=created_at,
                                    updated_at=created_at, instagram_data=instagram, description=description,
                                    instagram_link=post_url)


@shared_task
def delete_not_updated_posts_from_instagram(organization_id: int):
    ShopItem.objects.filter(organization_id=organization_id, name='Instagram', updated_at=F('created_at')).delete()
