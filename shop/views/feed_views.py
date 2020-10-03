from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from shop.filters import FeedItemFilter
from shop.models import ShopItem
from shop.serializers.item_serializers import ItemFeedSerializer


class FeedView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemFeedSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter, SearchFilter,)
    filterset_fields = ('subcategory', 'subcategory__category', 'organization__country', 'organization__city',)
    ordering_fields = ['updated_at', 'price']
    ordering = ['-updated_at']
    search_fields = ('name',)
    filter_class = FeedItemFilter

    def get_queryset(self):
        return ShopItem.objects.filter(is_published=True)
