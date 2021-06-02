from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from common.exceptions import NotAcceptableException
from organizations.serializers.query_param_serializers import OrganizationQueryParamSerializer
from shop.filters import FeedItemFilter, FeedItemOrderingFilter, FeedItemFilterWithoutOrganization
from shop.models import ShopItem
from shop.serializers.item_serializers import ItemFeedSerializer, StartDateTimeSerializer, SubscriptionItemSerializer
from shop.services.item_services import ShopItemService


class FeedView(ListAPIView):
    serializer_class = ItemFeedSerializer
    filter_backends = (DjangoFilterBackend, FeedItemOrderingFilter, SearchFilter,)
    filterset_fields = ('subcategory', 'subcategory__category', 'organization__country', 'organization__city',)
    ordering_fields = ['updated_at', 'price']
    ordering = ['-updated_at']
    search_fields = ('article', 'id', 'name', 'description',)
    filter_class = FeedItemFilter

    def get_queryset(self):
        search = self.request.GET.get('search', None)
        qs = ShopItem.objects.exclude(Q(organization__is_banned=True) | Q(organization__is_deleted=True))
        if search and search[0] == '#':  # Search among posts if hashtag is used
            qs = qs.filter(is_published=True)
        else:
            qs = qs.filter(is_published=True, price__isnull=False)

        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)


class OrganizationItemListView(FeedView):
    serializer_class = ItemFeedSerializer
    filter_class = FeedItemFilterWithoutOrganization

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid organization is required in query parameters'))
        organization = serializer.validated_data['organization']
        if organization.is_deleted:
            return ShopItem.objects.none()

        qs = ShopItemService.get_organization_items_queryset_for_user(
            organization=serializer.validated_data['organization'], user=self.request.user
        )
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)


class SubscriptionItemListView(FeedView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionItemSerializer

    def get_queryset(self):
        qs = ShopItemService.get_items_of_subscribed_organizations(user=self.request.user)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = StartDateTimeSerializer(data=request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Validation Error'))
        response = super().list(request, args, kwargs)
        response.data['has_new'] = ShopItemService.has_new(timestamp=serializer.validated_data['start_time'],
                                                           user=request.user)
        return response
