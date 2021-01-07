import datetime

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.serializers.query_param_serializers import OrganizationQueryParamSerializer
from shop.filters import FeedItemFilter, FeedItemOrderingFilter
from shop.models import ShopItem
from shop.serializers.item_serializers import ItemFeedSerializer, ItemListSerializer, \
    StartDateTimeSerializer
from shop.services.item_services import ShopItemService


class FeedView(ListAPIView):
    serializer_class = ItemFeedSerializer
    filter_backends = (DjangoFilterBackend, FeedItemOrderingFilter, SearchFilter,)
    filterset_fields = ('subcategory', 'subcategory__category', 'organization__country', 'organization__city',)
    ordering_fields = ['updated_at', 'price']
    ordering = ['-updated_at']
    search_fields = ('name', 'description',)
    filter_class = FeedItemFilter

    def get_queryset(self):
        qs = ShopItem.objects.filter(is_published=True)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)


class OrganizationItemListView(FeedView):
    serializer_class = ItemListSerializer

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException('Valid organization is required in query parameters')

        qs = ShopItemService.get_organization_items_queryset_for_user(
            organization=serializer.validated_data['organization'], user=self.request.user
        )
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)


class SubscriptionItemListView(FeedView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemFeedSerializer

    def get_queryset(self):
        qs = ShopItemService.get_items_of_subscribed_organizations(user=self.request.user)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = StartDateTimeSerializer(data=request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException('Validation Error')
        response = super().list(request, args, kwargs)
        response.data['has_new'] = ShopItemService.has_new(serializer.validated_data['start_time'])
        return response
