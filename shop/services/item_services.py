import json
import logging
from typing import Optional, Union
from django.db.models import Sum, Value, Q
from django.db.models.functions import Coalesce
from django.contrib.postgres.fields import ArrayField
from django.db.models import (
    BooleanField,
    Case,
    IntegerField,
    Max,
    Q,
    QuerySet,
    TextField,
    Value,
    When,
)
from django.db.models.expressions import RawSQL
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from organizations.models import Hotlink, Organization
from organizations.services.organization_services import OrganizationService
from organizations.services.subscription_services import SubscriptionService
from shop.models import ItemInstagramData, ShopItem, Ticket
from shop.services.cart_services import CartItemService
from transactions.models import Transaction
from users.models import User


logger = logging.getLogger(__name__)


class ShopItemService:
    @classmethod
    def _load_organization_catalog_json(cls, organization: Organization) -> Optional[list]:
        """Return parsed catalog JSON list or None when file is unavailable."""
        catalog_file = getattr(organization, "catalog_file", None)
        if not catalog_file:
            logger.info(
                "[SEARCH_SOURCE] org_id=%s source=db reason=catalog_file_missing",
                organization.id,
            )
            return None

        try:
            with catalog_file.open("rb") as catalog_stream:
                payload = json.load(catalog_stream)
        except Exception as exc:
            logger.warning(
                "[SEARCH_SOURCE] org_id=%s source=db reason=catalog_file_read_error error=%s",
                organization.id,
                exc,
            )
            return None

        if isinstance(payload, list):
            logger.info(
                "[SEARCH_SOURCE] org_id=%s source=file reason=catalog_file_loaded items=%s",
                organization.id,
                len(payload),
            )
            return payload

        logger.info(
            "[SEARCH_SOURCE] org_id=%s source=file reason=invalid_catalog_format",
            organization.id,
        )
        return []

    @classmethod
    def get(cls, **filters):
        try:
            return ShopItem.objects.get(**filters)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_("ShopItem not found"))

    @classmethod
    def update_published_status(cls, user: User, item: ShopItem, is_published: bool):
        if OrganizationService.user_can_edit_organization(
            user=user, organization=item.organization
        ) or OrganizationService.user_can_edit_own_resume(
            user=user, organization=item.organization
        ):
            if not is_published:
                CartItemService.delete_item_from_all_carts(item=item)
            item.is_published = is_published
            item.save(update_fields=("is_published",))
        else:
            raise NotAcceptableException(_("No rights to edit this item"))

    @classmethod
    def update_comments_disabled_status(
        cls, user: User, item: ShopItem, is_disabled: bool
    ):
        if OrganizationService.user_can_edit_organization(
            user=user, organization=item.organization
        ) or OrganizationService.user_can_edit_own_resume(
            user=user, organization=item.organization
        ):
            item.comments_disabled = is_disabled
            item.save(update_fields=("comments_disabled",))
        else:
            raise NotAcceptableException(_("No rights to edit this item"))

    @classmethod
    def subscription_has_new_items(cls, timestamp: str, user: User) -> bool:
        organizations = SubscriptionService.get_user_subscriptions(user=user)
        queryset = ShopItem.objects.filter(
            organization__in=organizations, is_published=True, updated_at__gt=timestamp
        ).distinct()
        return queryset.exists()

    @classmethod
    def feed_has_new_items(cls, timestamp: str) -> bool:
        queryset = ShopItem.objects.filter(
            is_published=True, price__isnull=False, updated_at__gt=timestamp
        ).exclude(Q(organization__is_banned=True) | Q(organization__is_deleted=True))
        return queryset.exists()

    @classmethod
    def annotate_likes_and_bookmarks(cls, queryset: QuerySet, user: User) -> QuerySet:
        if not user.is_authenticated:
            return queryset.annotate(
                is_liked=Value(False, output_field=BooleanField()),
                is_bookmarked=Value(False, output_field=BooleanField()),
            )

        return queryset.annotate(
            is_liked=Max(
                Case(
                    When(liked_users__user=user, then=1),
                    default=0,
                    output_field=BooleanField(),
                )
            ),
            is_bookmarked=Max(
                Case(
                    When(bookmarked_users__user=user, then=1),
                    default=0,
                    output_field=BooleanField(),
                )
            ),
        )

    @classmethod
    def get_organization_items_queryset_for_user(
        cls,
        organization: Organization,
        user: User,
        search: Union[str, None] = None,
        subcategory_id: Union[str, None] = None,
        without_price: Union[bool, None] = None,
        ordering: Union[str, None] = None,
    ) -> QuerySet:
        base_filters = Q()
        if search:
            base_filters &= Q(name__icontains=search)

        if subcategory_id:
            base_filters &= Q(subcategory_id=subcategory_id)

        if without_price:
            base_filters &= Q(price__isnull=False)

        can_see_own_unpublished = (
            user.is_authenticated
            and OrganizationService.user_can_edit_organization(
                user=user, organization=organization
            )
        )

        if organization.items_group is not None:
            if not can_see_own_unpublished:
                base_filters &= Q(
                    organization__in=organization.items_group.organizations.values_list(
                        "id"
                    ),
                    is_published=True,
                )
            else:
                base_filters &= Q(organization=organization) | Q(
                    organization__in=organization.items_group.organizations.values_list(
                        "id"
                    )
                )
            queryset = ShopItem.objects.filter(base_filters)
        else:
            queryset = ShopItem.objects.filter(base_filters, organization=organization)
            if not can_see_own_unpublished:
                queryset = queryset.exclude(is_published=False)

        queryset = queryset.annotate(
            annotated_total_stock=Coalesce(Sum('shop_item_size_counts__count'), Value(0))
        )
        queryset = queryset.distinct()

        if ordering == "price":
            return queryset.order_by("price")
        if ordering == "-price":
            return queryset.order_by("-price")
        return queryset.order_by("-updated_at", "-created_at")

    @classmethod
    def get_organization_rentals_queryset_for_user(
        cls, organization: Organization, user: User
    ) -> QuerySet:
        can_see_own_unpublished = (
            user.is_authenticated
            and OrganizationService.user_can_edit_organization(
                user=user, organization=organization
            )
        )

        exclude_condition = Q(user_bookings__transaction__type=Transaction.OFFLINE) & Q(
            user_bookings__transaction__status=Transaction.IN_PROGRESS
        )

        if organization.items_group is not None:
            if not can_see_own_unpublished:
                queryset = ShopItem.objects.filter(
                    organization__in=organization.items_group.organizations.values_list(
                        "id"
                    ),
                    is_published=True,
                    purchase_type=ShopItem.RENTAL,
                    user_bookings__transaction__client=user,
                ).exclude(exclude_condition)
            else:
                queryset = ShopItem.objects.filter(
                    Q(organization=organization)
                    | Q(
                        organization__in=organization.items_group.organizations.values_list(
                            "id"
                        )
                    ),
                    purchase_type=ShopItem.RENTAL,
                    user_bookings__transaction__client=user,
                ).exclude(exclude_condition)
        else:
            queryset = ShopItem.objects.filter(
                organization=organization,
                purchase_type=ShopItem.RENTAL,
                user_bookings__transaction__client=user,
            ).exclude(exclude_condition)
            if not can_see_own_unpublished:
                queryset = queryset.exclude(is_published=False)
        return queryset.distinct()

    @classmethod
    def get_organization_tickets_queryset_for_user(
        cls, organization: Organization, user: User
    ) -> QuerySet:
        can_see_own_unpublished = (
            user.is_authenticated
            and OrganizationService.user_can_edit_organization(
                user=user, organization=organization
            )
        )

        if organization.items_group is not None:
            if not can_see_own_unpublished:
                queryset = ShopItem.objects.filter(
                    organization__in=organization.items_group.organizations.values_list(
                        "id"
                    ),
                    is_published=True,
                    purchase_type=ShopItem.TICKET,
                )
            else:
                queryset = ShopItem.objects.filter(
                    Q(organization=organization)
                    | Q(
                        organization__in=organization.items_group.organizations.values_list(
                            "id"
                        )
                    ),
                    purchase_type=ShopItem.TICKET,
                )
        else:
            queryset = ShopItem.objects.filter(
                organization=organization, purchase_type=ShopItem.TICKET
            )
            if not can_see_own_unpublished:
                queryset = queryset.exclude(
                    is_published=False, purchase_type=ShopItem.TICKET
                )

        return queryset.distinct()

    @classmethod
    def get_organization_own_tickets_queryset_for_user(
        cls, organization: Organization, user: User
    ) -> QuerySet:
        can_see_own_unpublished = (
            user.is_authenticated
            and OrganizationService.user_can_edit_organization(
                user=user, organization=organization
            )
        )

        if organization.items_group is not None:
            if not can_see_own_unpublished:
                queryset = ShopItem.objects.filter(
                    organization__in=organization.items_group.organizations.values_list(
                        "id"
                    ),
                    is_published=True,
                    purchase_type=ShopItem.TICKET,
                )
            else:
                queryset = ShopItem.objects.filter(
                    Q(organization=organization)
                    | Q(
                        organization__in=organization.items_group.organizations.values_list(
                            "id"
                        )
                    ),
                    purchase_type=ShopItem.TICKET,
                )
        else:
            queryset = ShopItem.objects.filter(
                organization=organization, purchase_type=ShopItem.TICKET
            )
            if not can_see_own_unpublished:
                queryset = queryset.exclude(
                    is_published=False, purchase_type=ShopItem.TICKET
                )
        tickets = Ticket.objects.filter(organization=organization)
        shop_item_ids = tickets.values_list("item", flat=True).distinct()

        # Get the ShopItems corresponding to the ticket IDs
        queryset = queryset.filter(id__in=shop_item_ids)

        return queryset.distinct()

    @classmethod
    def get_items_of_subscribed_organizations(cls, user: User) -> QuerySet:
        organizations = SubscriptionService.get_user_subscriptions(user=user)
        queryset = ShopItem.objects.filter(
            organization__in=organizations,
            is_published=True,
            organization__is_banned=False,
        ).distinct()
        return queryset

    @classmethod
    def get_items_in_hotlink_collection(cls, hotlink: Hotlink) -> QuerySet:
        hotlink_subcategories = hotlink.collection_subcategories.values_list(
            "subcategory_id", flat=True
        )
        subcategory_items = ShopItem.objects.filter(
            subcategory__in=hotlink_subcategories
        )

        if hotlink.organization.items_group is None:
            subcategory_items = subcategory_items.filter(
                organization=hotlink.organization
            )
        else:
            subcategory_items = subcategory_items.filter(
                organization__in=hotlink.organization.items_group.organizations.values_list(
                    "id"
                )
            )

        shop_item_ids = (
            hotlink.collection_items.values_list("item_id", flat=True)
            .union(hotlink.collection_links.values_list("linked_item_id", flat=True))
            .union(subcategory_items.values_list("id", flat=True))
        )
        return (
            ShopItem.objects.filter(is_published=True, id__in=shop_item_ids)
            .distinct()
            .order_by("-updated_at")
        )

    @classmethod
    def get_liked_items(cls, user: User):
        return (
            ShopItem.objects.filter(
                is_published=True,
                liked_users__user=user,
                organization__is_deleted=False,
            )
            .order_by("-liked_users")
            .distinct()
        )

    @classmethod
    def get_bookmarked_items(cls, user: User):
        return (
            ShopItem.objects.filter(
                is_published=True,
                bookmarked_users__user=user,
                organization__is_deleted=False,
            )
            .order_by("-bookmarked_users")
            .distinct()
        )

    @classmethod
    def delete_instagram_images(cls, item_id):
        item = ShopItem.objects.get(id=int(item_id))
        return ItemInstagramData.objects.filter(item=item, video_url=None).delete()

    @classmethod
    def delete_instagram_video(cls, item_id):
        item = ShopItem.objects.get(id=int(item_id))
        return ItemInstagramData.objects.filter(
            item=item, video_url__isnull=False
        ).delete()

    @classmethod
    def delete_expired_posts(cls):
        ShopItem.objects.filter(
            name="Instagram",
            article=None,
            instagram_data__isnull=True,
            images__isnull=True,
        ).delete()

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
        for i in range(len(response.data.get("list"))):
            if (
                response.data.get("list")[i].get("name") not in array_items
                and i <= limit_of_items
            ):
                array_items.append(response.data.get("list")[i].get("name"))
            else:
                pop_index.append(i)
        for i in range(len(response.data.get("list")) - 1, -1, -1):
            if i in pop_index:
                response.data.get("list").pop(i)
        response.data["count"] = len(array_items)
        response.data["results"] = response.data.pop("list")
        del response.data["total_count"]
        del response.data["total_pages"]

        return response

    @classmethod
    def get_ordering_search_result(cls, queryset: QuerySet, search_word: str) -> QuerySet:
        search_word = search_word.strip()
        logger.info(
            "[SEARCH_SOURCE] source=db mode=direct_db_search search=%s",
            search_word,
        )

        queryset = queryset.filter(
            Q(name__icontains=search_word) |
            Q(description__icontains=search_word) |
            Q(article__icontains=search_word)
        )

        queryset = queryset.annotate(
            arr_name=RawSQL(
                "string_to_array(lower(\"name\"), ' ')",
                params=(),
                output_field=ArrayField(base_field=TextField())
            ),
            name_order=Case(
                When(name__iexact=search_word, then=1),
                When(arr_name__contains=[search_word.lower()], then=2),
                When(name__icontains=search_word, then=3),
                When(description__icontains=search_word, then=4),
                When(article__icontains=search_word, then=5),
                default=Value(6),
                output_field=IntegerField(),
            ),
        ).order_by(
            "name_order",
            "-updated_at",
        )

        return queryset

    @classmethod
    def get_ordering_search_result_in_catalog_file(
        cls,
        queryset: QuerySet,
        search_word: str,
        organization: Organization,
    ) -> QuerySet:
        """
        Search items inside organization catalog JSON file and keep API output based on DB queryset.
        Falls back to DB search only when catalog file is unavailable.
        """
        search_word = search_word.strip()
        if not search_word:
            logger.info(
                "[SEARCH_SOURCE] org_id=%s source=db reason=empty_search_word",
                organization.id,
            )
            return queryset

        catalog_items = cls._load_organization_catalog_json(organization=organization)
        if catalog_items is None:
            logger.info(
                "[SEARCH_SOURCE] org_id=%s source=db reason=fallback_from_file_search search=%s",
                organization.id,
                search_word,
            )
            return cls.get_ordering_search_result(queryset=queryset, search_word=search_word)

        logger.info(
            "[SEARCH_SOURCE] org_id=%s source=file reason=search_in_catalog_json search=%s",
            organization.id,
            search_word,
        )

        search_lower = search_word.lower()
        scored_ids = []

        for raw_item in catalog_items:
            if not isinstance(raw_item, dict):
                continue

            item_id = raw_item.get("id")
            if item_id in (None, ""):
                continue

            try:
                item_id = int(item_id)
            except (TypeError, ValueError):
                continue

            name = str(raw_item.get("name") or "")
            description = str(raw_item.get("description") or "")
            article = str(raw_item.get("article") or "")

            name_lower = name.lower()
            description_lower = description.lower()
            article_lower = article.lower()

            if name_lower == search_lower:
                rank = 1
            elif search_lower in name_lower.split():
                rank = 2
            elif search_lower in name_lower:
                rank = 3
            elif search_lower in description_lower:
                rank = 4
            elif search_lower in article_lower:
                rank = 5
            else:
                continue

            scored_ids.append((rank, item_id))

        if not scored_ids:
            logger.info(
                "[SEARCH_SOURCE] org_id=%s source=file result=no_matches search=%s",
                organization.id,
                search_word,
            )
            return queryset.none()

        scored_ids.sort(key=lambda pair: pair[0])

        ordered_ids = []
        seen = set()
        for _, item_id in scored_ids:
            if item_id in seen:
                continue
            seen.add(item_id)
            ordered_ids.append(item_id)

        order_case = Case(
            *[When(id=item_id, then=position) for position, item_id in enumerate(ordered_ids)],
            default=Value(len(ordered_ids)),
            output_field=IntegerField(),
        )

        logger.info(
            "[SEARCH_SOURCE] org_id=%s source=file result=matched matched_count=%s search=%s",
            organization.id,
            len(ordered_ids),
            search_word,
        )

        return queryset.filter(id__in=ordered_ids).annotate(file_order=order_case).order_by(
            "file_order", "-updated_at"
        )

    @classmethod
    def get_user_resumes(cls, user: User):
        return ShopItem.objects.filter(user=user)
