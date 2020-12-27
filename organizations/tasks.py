from django.db.models import F
from instagram_parsers.parsers import parser
from shop.models import ShopItem, ItemInstagramData
from celery import shared_task
from organizations.models import Organization, InstagramIntegration


@shared_task
def parse_instagram_to_shop_items(organization_id: int):
    organization = Organization.objects.get(id=organization_id)
    instagram_integration = InstagramIntegration.objects.get(organization=organization)
    instagram_posts = parser.get_posts(instagram_integration.account_user_id)
    for instagram in instagram_posts:
        if not ShopItem.objects.filter(
                created_at=instagram.get('created_at'),
                organization=organization):
            description = instagram.pop('description')
            created_at = instagram.pop('created_at')
            post_url = instagram.pop('post_url')
            shop_item = ShopItem.objects.create(name="Instagram", organization=organization, created_at=created_at,
                                                updated_at=created_at, description=description, instagram_link=post_url)
            for data in instagram.get('data'):
                ItemInstagramData.objects.create(item=shop_item, post_pk=data.get('pk'),
                                                 thumbnail_url=data.get('thumbnail_url'),
                                                 video_url=data.get('video_url'))


@shared_task
def delete_not_updated_posts_from_instagram(organization_id: int):
    ShopItem.objects.filter(organization_id=organization_id, name='Instagram', updated_at=F('created_at')).delete()


@shared_task
def parse_instagram_last_updates(organization_id: int):
    organization = Organization.objects.get(id=organization_id)
    instagram_integration = InstagramIntegration.objects.get(organization=organization)
    if instagram_integration:
        latest_instagram_shop_item = ShopItem.objects.filter(organization_id=organization_id).exclude(
            instagram_data__isnull=True).order_by('-created_at').first()
        instagram_posts = parser.get_latest_posts(user_id=instagram_integration.account_user_id,
                                                  latest_update=str(latest_instagram_shop_item.created_at))
        for instagram in instagram_posts:
            if not ShopItem.objects.filter(
                    created_at=instagram.get('created_at'),
                    organization=organization):
                description = instagram.pop('description')
                created_at = instagram.pop('created_at')
                post_url = instagram.pop('post_url')
                ShopItem.objects.create(name="Instagram", organization=organization, created_at=created_at,
                                        updated_at=created_at, instagram_data=instagram, description=description,
                                        instagram_link=post_url)
