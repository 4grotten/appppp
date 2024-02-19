from django.contrib.postgres.fields import ArrayField
from django.db.models import QuerySet, Case, When, BooleanField, Value, Max, Q, IntegerField, TextField
from django.db.models.expressions import RawSQL
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.contrib.gis.geos import Point

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from organizations.models import Organization, Hotlink
from organizations.services.organization_services import OrganizationService
from organizations.services.subscription_services import SubscriptionService
from shop.models import ShopItem, ItemInstagramData, Ticket, Booking
from shop.services.cart_services import CartItemService
from transactions.models import Transaction
from users.models import User


class ShopItemService:
    @classmethod
    def get(cls, **filters):
        try:
            return ShopItem.objects.get(**filters)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

    @classmethod
    def update_published_status(cls, user: User, item: ShopItem, is_published: bool):
        if OrganizationService.user_can_edit_organization(user=user, organization=item.organization) or \
                OrganizationService.user_can_edit_own_resume(user=user, organization=item.organization):
            if not is_published:
                CartItemService.delete_item_from_all_carts(item=item)
            item.is_published = is_published
            item.save(update_fields=('is_published',))
        else:
            raise NotAcceptableException(_('No rights to edit this item'))

    @classmethod
    def subscription_has_new_items(cls, timestamp: str, user: User) -> bool:
        organizations = SubscriptionService.get_user_subscriptions(user=user)
        queryset = ShopItem.objects.filter(organization__in=organizations, is_published=True,
                                           updated_at__gt=timestamp).distinct()
        return queryset.exists()

    @classmethod
    def feed_has_new_items(cls, timestamp: str) -> bool:
        queryset = ShopItem.objects.filter(is_published=True, price__isnull=False, updated_at__gt=timestamp).exclude(
            Q(organization__is_banned=True) | Q(organization__is_deleted=True))
        return queryset.exists()

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
        can_see_own_unpublished = user.is_authenticated and OrganizationService.user_can_edit_organization(
            user=user, organization=organization)

        if organization.items_group is not None:
            if not can_see_own_unpublished:
                queryset = ShopItem.objects.filter(
                    organization__in=organization.items_group.organizations.values_list('id'), is_published=True
                )
            else:
                queryset = ShopItem.objects.filter(
                    Q(organization=organization) |
                    Q(organization__in=organization.items_group.organizations.values_list('id'))
                )
        else:
            queryset = ShopItem.objects.filter(organization=organization)
            if not can_see_own_unpublished:
                queryset = queryset.exclude(is_published=False)

        return queryset.distinct()

    @classmethod
    def get_organization_rentals_queryset_for_user(cls, organization: Organization, user: User) -> QuerySet:
        can_see_own_unpublished = user.is_authenticated and OrganizationService.user_can_edit_organization(
            user=user, organization=organization)

        exclude_condition = Q(user_bookings__transaction__type=Transaction.OFFLINE) & \
                            Q(user_bookings__transaction__status=Transaction.IN_PROGRESS)

        if organization.items_group is not None:
            if not can_see_own_unpublished:
                queryset = ShopItem.objects.filter(
                    organization__in=organization.items_group.organizations.values_list('id'), is_published=True,
                    purchase_type=ShopItem.RENTAL, user_bookings__transaction__client=user
                ).exclude(exclude_condition)
            else:
                queryset = ShopItem.objects.filter(
                    Q(organization=organization) |
                    Q(organization__in=organization.items_group.organizations.values_list('id')),
                    purchase_type=ShopItem.RENTAL,
                    user_bookings__transaction__client=user
                ).exclude(exclude_condition)
        else:
            queryset = ShopItem.objects.filter(organization=organization, purchase_type=ShopItem.RENTAL,
                                               user_bookings__transaction__client=user).exclude(exclude_condition)
            if not can_see_own_unpublished:
                queryset = queryset.exclude(is_published=False)
        return queryset.distinct()

    @classmethod
    def get_organization_tickets_queryset_for_user(cls, organization: Organization, user: User) -> QuerySet:
        can_see_own_unpublished = user.is_authenticated and OrganizationService.user_can_edit_organization(
            user=user, organization=organization)

        if organization.items_group is not None:
            if not can_see_own_unpublished:
                queryset = ShopItem.objects.filter(
                    organization__in=organization.items_group.organizations.values_list('id'), is_published=True,
                    purchase_type=ShopItem.TICKET
                )
            else:
                queryset = ShopItem.objects.filter(
                    Q(organization=organization) |
                    Q(organization__in=organization.items_group.organizations.values_list('id')),
                    purchase_type=ShopItem.TICKET
                )
        else:
            queryset = ShopItem.objects.filter(organization=organization, purchase_type=ShopItem.TICKET)
            if not can_see_own_unpublished:
                queryset = queryset.exclude(is_published=False, purchase_type=ShopItem.TICKET)

        return queryset.distinct()

    @classmethod
    def get_organization_own_tickets_queryset_for_user(cls, organization: Organization, user: User) -> QuerySet:
        can_see_own_unpublished = user.is_authenticated and OrganizationService.user_can_edit_organization(
            user=user, organization=organization)

        if organization.items_group is not None:
            if not can_see_own_unpublished:
                queryset = ShopItem.objects.filter(
                    organization__in=organization.items_group.organizations.values_list('id'), is_published=True,
                    purchase_type=ShopItem.TICKET
                )
            else:
                queryset = ShopItem.objects.filter(
                    Q(organization=organization) |
                    Q(organization__in=organization.items_group.organizations.values_list('id')),
                    purchase_type=ShopItem.TICKET,
                )
        else:
            queryset = ShopItem.objects.filter(organization=organization, purchase_type=ShopItem.TICKET)
            if not can_see_own_unpublished:
                queryset = queryset.exclude(is_published=False, purchase_type=ShopItem.TICKET)
        tickets = Ticket.objects.filter(organization=organization)
        shop_item_ids = tickets.values_list('item', flat=True).distinct()

        # Get the ShopItems corresponding to the ticket IDs
        queryset = queryset.filter(id__in=shop_item_ids)

        return queryset.distinct()

    @classmethod
    def get_items_of_subscribed_organizations(cls, user: User) -> QuerySet:
        organizations = SubscriptionService.get_user_subscriptions(user=user)
        queryset = ShopItem.objects.filter(organization__in=organizations, is_published=True, organization__is_banned=False).distinct()
        return queryset

    @classmethod
    def get_items_in_hotlink_collection(cls, hotlink: Hotlink) -> QuerySet:
        hotlink_subcategories = hotlink.collection_subcategories.values_list('subcategory_id', flat=True)
        subcategory_items = ShopItem.objects.filter(subcategory__in=hotlink_subcategories)

        if hotlink.organization.items_group is None:
            subcategory_items = subcategory_items.filter(organization=hotlink.organization)
        else:
            subcategory_items = subcategory_items.filter(
                organization__in=hotlink.organization.items_group.organizations.values_list('id')
            )

        shop_item_ids = hotlink.collection_items.values_list('item_id', flat=True).union(
            hotlink.collection_links.values_list('linked_item_id', flat=True)).union(
            subcategory_items.values_list('id', flat=True)
        )
        return ShopItem.objects.filter(is_published=True, id__in=shop_item_ids).distinct().order_by('-updated_at')

    @classmethod
    def get_liked_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, liked_users__user=user,
                                       organization__is_deleted=False).order_by('-liked_users').distinct()

    @classmethod
    def get_bookmarked_items(cls, user: User):
        return ShopItem.objects.filter(is_published=True, bookmarked_users__user=user,
                                       organization__is_deleted=False).order_by('-bookmarked_users').distinct()

    @classmethod
    def delete_instagram_images(cls, item_id):
        item = ShopItem.objects.get(id=int(item_id))
        return ItemInstagramData.objects.filter(item=item, video_url=None).delete()

    @classmethod
    def delete_instagram_video(cls, item_id):
        item = ShopItem.objects.get(id=int(item_id))
        return ItemInstagramData.objects.filter(item=item, video_url__isnull=False).delete()

    @classmethod
    def delete_expired_posts(cls):
        ShopItem.objects.filter(name='Instagram', article=None, instagram_data__isnull=True, images__isnull=True).delete()

    @classmethod
    def change_updated_at_and_is_updated_and_removed_at_field(cls, item_id):
        item = ShopItem.objects.get(id=int(item_id))
        item.removed_at = None
        item.is_updated = True
        item.updated_at = now()
        item.save()

    @classmethod
    def get_suggest_items(cls, response):

        array_items = []
        pop_index = []
        limit_of_items = 19
        for i in range(len(response.data.get('list'))):
            if response.data.get('list')[i].get('name') not in array_items and i <= limit_of_items:
                array_items.append(response.data.get('list')[i].get('name'))
            else:
                pop_index.append(i)
        for i in range(len(response.data.get('list')) - 1, -1, -1):
            if i in pop_index:
                response.data.get('list').pop(i)
        response.data['count'] = len(array_items)
        response.data['results'] = response.data.pop('list')
        del response.data['total_count']
        del response.data['total_pages']

        return response

    @classmethod
    def get_ordering_search_result(cls, queryset: QuerySet, search_word: str) -> QuerySet:
        queryset = queryset.annotate(
            arr_name=RawSQL("string_to_array(lower('name'), ' ')", output_field=ArrayField(base_field=TextField()), params=()),
            name_order=Case(
            When(name__iexact=search_word, then=1),
            When(arr_name__contains=[search_word.lower()], then=2),
            When(name__icontains=search_word, then=3),
            When(description__icontains=search_word, then=4),
            When(article__icontains=search_word, then=5),
            default=Value(6),
            output_field=IntegerField(),
        )).order_by('name_order', '-updated_at', )

        return queryset


    @classmethod
    def get_user_resumes(cls, user: User):
        return ShopItem.objects.filter(user=user)