from typing import Union

from django.db.models import QuerySet, Count, Q

from common.models import City, Country
from organizations.models import Service, Organization
from organizations.services.common_shop_item_services import CommonItemsGroupService
from organizations.services.organization_services import OrganizationService
from shop.models import ItemSubcategory, ItemCategory


class ItemCategoryService:
    @classmethod
    def get_general_nonempty_category_ids(cls, country: Union[Country, None], city: Union[City, None]) -> list:
        item_filters = Q(items_in_category__is_published=True) & Q(items_in_category__price__isnull=False)

        if city is not None:
            item_filters = item_filters & Q(items_in_category__organization__city=city)
        elif country is not None:
            item_filters = item_filters & Q(items_in_category__organization__country=country)

        return ItemSubcategory.objects.filter(organization__isnull=True).annotate(
            items_count=Count('items_in_category', item_filters)
        ).filter(items_count__gt=0).values_list('category__id', flat=True)

    @classmethod
    def get_general_nonempty_service_subcategory_ids(cls, service: Union[Service, None], country: Union[Country, None],
                                                     city: Union[City, None]) -> list:
        item_filters = Q(items_in_category__is_published=True) & Q(items_in_category__price__isnull=False) & Q(
            items_in_category__organization__is_banned=False) & Q(items_in_category__organization__is_deleted=False)

        if city is not None:
            item_filters = item_filters & Q(items_in_category__organization__city=city)
        elif country is not None:
            item_filters = item_filters & Q(items_in_category__organization__country=country)

        org = Organization.objects.filter(types__services=service).values_list('id', flat=True)
        # for i in org:
        #     print(i)
        # print(org, 'orggg')
        org_cat = ItemSubcategory.objects.filter(items_in_category__organization__id__in=org,
                                                 organization__isnull=True).values_list(
            'id', flat=True).distinct()
        #
        # print(org_cat, 'org_cat')

        item_cat = ItemSubcategory.objects.filter(category__services=service, organization__isnull=True).annotate(
            items_count=Count('items_in_category', item_filters)) \
            .filter(items_count__gt=0).values_list('id', flat=True)

        # print(item_cat, 'item_cat')
        # # org_cat = ItemSubcategory.objects.filter(category__services=service, organization__isnull=True).annotate(
        # #     items_count=Count('items_in_category', item_filters)) \
        # #     .filter(items_count__gt=0).values_list('id', flat=True)
        #
        # # Service shop_item categories
        # print(list(set(org_cat) & set(item_cat)))
        return list(set(org_cat) & set(item_cat))

    @classmethod
    def get_nonempty_general_categories(cls, country: Union[Country, None], city: Union[City, None]) -> QuerySet:
        category_ids = cls.get_general_nonempty_category_ids(country=country, city=city)
        return ItemCategory.objects.filter(id__in=category_ids).order_by('name')

    @classmethod
    def get_nonempty_general_service_categories(cls, service: Union[Service, None], country: Union[Country, None],
                                                city: Union[City, None]) -> QuerySet:
        category_ids = cls.get_general_nonempty_service_subcategory_ids(service=service, country=country, city=city)
        return ItemSubcategory.objects.filter(id__in=category_ids).order_by('category__id')


class ItemSubcategoryService:
    @classmethod
    def get_orgs_nonempty_subcategories(cls, organization_id: int) -> QuerySet:
        organization = OrganizationService.get(id=organization_id)
        common_item_partner_ids = CommonItemsGroupService.get_partners_with_common_items(organization=organization)
        common_item_partner_ids.append(organization_id)

        subcategories = ItemSubcategory.objects.filter(
            Q(organization__isnull=True) | Q(organization_id__in=common_item_partner_ids)
        )
        item_filters = Q(items_in_category__is_published=True) & Q(
            items_in_category__organization_id__in=common_item_partner_ids
        )

        return subcategories.annotate(items_count=Count('items_in_category', item_filters)).filter(items_count__gt=0)

    @classmethod
    def get_general_nonempty_subcategories_in_category(cls, category: ItemCategory, country: Union[Country, None],
                                                       city: Union[City, None]) -> QuerySet:
        subcategories = ItemSubcategory.objects.filter(organization__isnull=True, category=category) \
            .exclude(Q(items_in_category__organization__is_banned=True)
                     | Q(items_in_category__organization__is_deleted=True))
        item_filters = Q(items_in_category__is_published=True) & Q(items_in_category__price__isnull=False)
        if city is not None:
            item_filters = item_filters & Q(items_in_category__organization__city=city)
        elif country is not None:
            item_filters = item_filters & Q(items_in_category__organization__country=country)

        return subcategories.annotate(items_count=Count('items_in_category', item_filters)).filter(items_count__gt=0)
