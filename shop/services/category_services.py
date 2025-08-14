from typing import Union

from django.db.models import QuerySet, Count, Q, Subquery, OuterRef

from common.models import City, Country
from organizations.models import Service, Organization
from organizations.services.common_shop_item_services import CommonItemsGroupService
from organizations.services.organization_services import OrganizationService
from shop.models import ItemSubcategory, ItemCategory, ShopItem
import logging


class ItemCategoryService:
    @classmethod
    def get_general_nonempty_category_ids(
        cls, country: Union[Country, None], city: Union[City, None]
    ) -> list:
        item_filters = Q(items_in_category__is_published=True) & Q(
            items_in_category__price__isnull=False
        )

        if city is not None:
            item_filters = item_filters & Q(items_in_category__organization__city=city)
        elif country is not None:
            item_filters = item_filters & Q(
                items_in_category__organization__country=country
            )

        return (
            ItemSubcategory.objects.filter(organization__isnull=True)
            .annotate(items_count=Count("items_in_category", item_filters))
            .filter(items_count__gt=0)
            .values_list("category__id", flat=True)
        )

    @classmethod
    def get_general_nonempty_service_subcategory_ids(
        cls,
        service: Union[Service, None],
        country: Union[Country, None],
        city: Union[City, None],
    ) -> list:
        if not service:
            return []

        if isinstance(service, int):
            try:
                service = Service.objects.get(id=service)
            except Service.DoesNotExist:
                return []

        if service.is_wholesale:
            item_filters = Q(
                items_in_category__is_published=True,
                items_in_category__price__isnull=False,
                items_in_category__organization__is_banned=False,
                items_in_category__organization__is_deleted=False,
                items_in_category__organization__is_wholesale=True,
                items_in_category__organization__types__services=service,
            )
            if city:
                item_filters &= Q(items_in_category__organization__city=city)
            elif country:
                item_filters &= Q(items_in_category__organization__country=country)

            return list(
                ItemSubcategory.objects.filter(organization__isnull=True)
                .annotate(
                    items_count=Count(
                        "items_in_category", filter=item_filters, distinct=True
                    )
                )
                .filter(items_count__gt=0)
                .values_list("id", flat=True)
                .distinct()
            )

        else:
            filters = {}
            item_filters = Q(
                items_in_category__is_published=True,
                items_in_category__price__isnull=False,
                items_in_category__organization__is_banned=False,
                items_in_category__organization__is_deleted=False,
            )

            if city:
                item_filters &= Q(items_in_category__organization__city=city)
                filters["city"] = city
            elif country:
                filters["country"] = country
                item_filters &= Q(items_in_category__organization__country=country)
            logging.warning(f"filters: {filters}")
            org_ids = Organization.objects.filter(
                types__services=service, **filters
            ).values_list("id", flat=True)
            logging.warning(f"org_ids: {org_ids}")
            org_subcategories = (
                ItemSubcategory.objects.filter(
                    items_in_category__organization__id__in=org_ids,
                    organization__isnull=True,
                    items_in_category__organization__country=country,
                    items_in_category__organization__city=city,
                )
                .values_list("id", flat=True)
                .distinct()
            )

            service_subcategories = (
                ItemSubcategory.objects.filter(
                    category__services=service, organization__isnull=True
                )
                .annotate(items_count=Count("items_in_category", filter=item_filters))
                .filter(items_count__gt=0)
                .values_list("id", flat=True)
            )
            ids = list(set(org_subcategories) & set(service_subcategories))
            return ids

    @classmethod
    def get_nonempty_general_categories(
        cls, country: Union[Country, None], city: Union[City, None]
    ) -> QuerySet:
        category_ids = cls.get_general_nonempty_category_ids(country=country, city=city)
        return (
            ItemCategory.objects.filter(id__in=category_ids)
            .annotate(count=Count("subcategories__items_in_category"))
            .order_by("-count")
        )

    @classmethod
    def get_nonempty_general_service_categories(
        cls,
        service: Union[Service, None],
        country: Union[Country, None],
        city: Union[City, None],
    ) -> QuerySet:
        category_ids = cls.get_general_nonempty_service_subcategory_ids(
            service=service, country=country, city=city
        )
        return ItemSubcategory.objects.filter(id__in=category_ids).order_by(
            "category__id"
        )


class ItemSubcategoryService:
    @classmethod
    def get_orgs_nonempty_subcategories(cls, organization_id: int) -> QuerySet:
        organization = OrganizationService.get(id=organization_id)
        common_item_partner_ids = (
            CommonItemsGroupService.get_partners_with_common_items(
                organization=organization
            )
        )
        common_item_partner_ids.append(organization_id)

        subcategories = ItemSubcategory.objects.filter(
            Q(organization__isnull=True)
            | Q(organization_id__in=common_item_partner_ids)
        )
        item_filters = Q(items_in_category__is_published=True) & Q(
            items_in_category__organization_id__in=common_item_partner_ids
        )

        return subcategories.annotate(
            items_count=Count("items_in_category", item_filters)
        ).filter(items_count__gt=0)

    @classmethod
    def get_general_nonempty_subcategories_in_category(
        cls,
        category: ItemCategory,
        country: Union[Country, None],
        city: Union[City, None],
    ) -> QuerySet:
        subcategories = ItemSubcategory.objects.filter(
            organization__isnull=True, category=category
        ).exclude(
            Q(items_in_category__organization__is_banned=True)
            & Q(items_in_category__organization__is_deleted=True)
        )
        item_filters = Q(items_in_category__is_published=True) & Q(
            items_in_category__price__isnull=False
        )
        if city is not None:
            item_filters = item_filters & Q(items_in_category__organization__city=city)
        elif country is not None:
            item_filters = item_filters & Q(
                items_in_category__organization__country=country
            )

        return subcategories.annotate(
            items_count=Count("items_in_category", item_filters)
        ).filter(items_count__gt=0)
