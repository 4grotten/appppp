from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter

from shop.models import ShopItem


class NumberInFilter(filters.BaseInFilter, filters.NumberFilter):
    pass


class FeedItemFilter(filters.FilterSet):
    subcategories = NumberInFilter(field_name='subcategory__id', lookup_expr='in')
    category = filters.NumberFilter(field_name='subcategory__category')
    country = filters.CharFilter(field_name='organization__country')
    city = filters.CharFilter(field_name='organization__city')
    current_timestamp_lt = filters.IsoDateTimeFilter(field_name='updated_at', lookup_expr='lt')

    class Meta:
        model = ShopItem
        fields = ['id', 'subcategories', 'organization', 'category', 'country', 'city', 'current_timestamp_lt']


class FeedItemFilterWithoutOrganization(FeedItemFilter):
    class Meta:
        model = ShopItem
        fields = ['id', 'subcategories', 'category', 'country', 'city', 'current_timestamp_lt']


class FeedItemOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)

        if ordering:
            if '-price' in ordering or 'price' in ordering:
                queryset = queryset.exclude(price__isnull=True)
            return queryset.order_by(*ordering)

        return queryset


class SuggestItemFilter(filters.FilterSet):
    country = filters.CharFilter(field_name='organization__country')

    class Meta:
        model = ShopItem
        fields = ['country', ]
