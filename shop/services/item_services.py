from django.db.models import QuerySet, Case, When, BooleanField, Value, Max, Q

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from organizations.services.subscription_services import SubscriptionService
from shop.models import ShopItem, ItemInstagramData
from shop.services.cart_services import CartItemService
from users.models import User


class ShopItemService:

    @classmethod
    def get(cls, **filters):
        try:
            return ShopItem.objects.get(**filters)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException('ShopItem not found')

    @classmethod
    def update_published_status(cls, user: User, item: ShopItem, is_published: bool):
        if not OrganizationService.user_can_edit_organization(user=user, organization=item.organization):
            raise NotAcceptableException('No rights to edit this item')
        if not is_published:
            CartItemService.delete_item_from_all_carts(item=item)
        item.is_published = is_published
        item.save(update_fields=('is_published',))

    @classmethod
    def annotate_likes_and_bookmarks(cls, queryset: QuerySet, user: User) -> QuerySet:
        if not user.is_authenticated:
            return queryset.annotate(
                is_liked=Value(False, output_field=BooleanField()),
                is_bookmarked=Value(False, output_field=BooleanField())
            )

        return queryset.annotate(
            is_liked=Max(Case(
                When(liked_users__user=user, then=1), default=0,
                output_field=BooleanField())
            ),
            is_bookmarked=Max(Case(
                When(bookmarked_users__user=user, then=1), default=0,
                output_field=BooleanField()
            ))
        )

    @classmethod
    def get_organization_items_queryset_for_user(cls, organization: Organization, user: User) -> QuerySet:
        queryset = ShopItem.objects.filter(organization=organization)

        if (user.is_authenticated and not OrganizationService.user_can_edit_organization(
                user=user, organization=organization)) or not user.is_authenticated:
            queryset = queryset.exclude(is_published=False)

        return queryset

    @classmethod
    def get_items_of_subscribed_organizations(cls, user: User) -> QuerySet:
        organizations = SubscriptionService.get_user_subscriptions(user=user)
        queryset = ShopItem.objects.filter(organization__in=organizations, is_published=True).distinct()
        return queryset

    @classmethod
    def get_liked_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, liked_users__user=user).order_by('-liked_users').distinct()

    @classmethod
    def get_bookmarked_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, bookmarked_users__user=user).order_by(
            '-bookmarked_users').distinct()

    @classmethod
    def delete_instagram_images(cls, item_id):
        item = ShopItem.objects.get(id=int(item_id))
        return ItemInstagramData.objects.filter(item=item, video_url='None').delete()
