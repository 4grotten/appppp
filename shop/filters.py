from django_filters import rest_framework as filters

from shop.models import ShopItem


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class FeedItemFilter(filters.FilterSet):
    subcategories = NumberInFilter(field_name='subcategory__id', lookup_expr='in')
    category = filters.NumberFilter(field_name='subcategory__category')
    country = filters.CharFilter(field_name='organization__country')
    city = filters.CharFilter(field_name='organization__city')

    class Meta:
        model = ShopItem
        fields = ['id', 'subcategories', 'organization', 'category', 'country', 'city']
