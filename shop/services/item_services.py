from django.db.models import QuerySet, Case, When, BooleanField, Value, Max

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem
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
    def get_organization_items_queryset_for_user(cls, organization: Organization, user: User):
        queryset = ShopItem.objects.filter(organization=organization)

        if user.is_authenticated and not OrganizationService.user_can_edit_organization(user=user,
                                                                                        organization=organization):
            queryset = queryset.exclude(is_published=False)

        return queryset

    @classmethod
    def get_liked_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, liked_users__user=user).distinct()

    @classmethod
    def get_bookmarked_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, bookmarked_users__user=user).distinct()
