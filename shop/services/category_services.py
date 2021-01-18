from typing import Union

from django.db.models import QuerySet, Count, Q

from common.models import City, Country
from shop.models import ItemSubcategory, ItemCategory


class ItemCategoryService:
    @classmethod
    def get_general_nonempty_category_ids(cls, country: Union[Country, None], city: Union[City, None]) -> list:
        item_filters = Q(items_in_category__is_published=True)

        if city is not None:
            item_filters = item_filters & Q(items_in_category__organization__city=city)
        elif country is not None:
            item_filters = item_filters & Q(items_in_category__organization__country=country)

        return ItemSubcategory.objects.filter(organization__isnull=True).annotate(
            items_count=Count('items_in_category', item_filters)
        ).filter(items_count__gt=0).values_list('category__id', flat=True)

    @classmethod
    def get_nonempty_general_categories(cls, country: Union[Country, None], city: Union[City, None]) -> QuerySet:
        category_ids = cls.get_general_nonempty_category_ids(country=country, city=city)
        return ItemCategory.objects.filter(id__in=category_ids).order_by('name')


class ItemSubcategoryService:
    @classmethod
    def get_orgs_nonempty_subcategories(cls, organization_id: int) -> QuerySet:
        subcategories = ItemSubcategory.objects.filter(
            Q(organization__isnull=True) | Q(organization_id=organization_id))

        item_filters = Q(items_in_category__is_published=True) & Q(items_in_category__organization_id=organization_id)

        return subcategories.annotate(items_count=Count('items_in_category', item_filters)).filter(items_count__gt=0)

    @classmethod
    def get_general_nonempty_subcategories_in_category(cls, category: ItemCategory, country: Union[Country, None],
                                                       city: Union[City, None]) -> QuerySet:
        subcategories = ItemSubcategory.objects.filter(organization__isnull=True, category=category)

        item_filters = Q(items_in_category__is_published=True)
        if city is not None:
            item_filters = item_filters & Q(items_in_category__organization__city=city)
        elif country is not None:
            item_filters = item_filters & Q(items_in_category__organization__country=country)

        return subcategories.annotate(items_count=Count('items_in_category', item_filters)).filter(items_count__gt=0)
