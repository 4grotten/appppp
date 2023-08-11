from django.db.models import Q, Case, When, Value, IntegerField
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly

from common.exceptions import NotAcceptableException
from organizations.constants import HOTLINK_COLLECTION
from organizations.models import OrganizationBlacklist, Organization
from organizations.serializers.query_param_serializers import OrganizationQueryParamSerializer
from organizations.services.hotlink_services import HotlinkService
from shop.filters import FeedItemFilter, FeedItemOrderingFilter, FeedItemFilterWithoutOrganization
from shop.models import ShopItem
from shop.serializers.item_serializers import ItemFeedSerializer, StartDateTimeSerializer, SubscriptionItemSerializer, \
    RentalTicketListSerializer
from shop.services.item_services import ShopItemService


class FeedView(ListAPIView):
    serializer_class = ItemFeedSerializer
    filter_backends = (DjangoFilterBackend, FeedItemOrderingFilter, SearchFilter,)
    filterset_fields = ('subcategory', 'subcategory__category', 'organization__country', 'organization__city',)
    ordering_fields = ['updated_at', 'price']
    search_fields = ('article', 'id', 'name', 'description',)
    filter_class = FeedItemFilter

    def get_queryset(self):
        search = self.request.GET.get('search', None)
        user = self.request.user
        if user.is_authenticated:
            organizations = Organization.objects.all()
            blacklist = OrganizationBlacklist.objects.filter(user=self.request.user, organization__in=organizations).values_list('organization_id', flat=True).distinct()
            qs = ShopItem.objects.exclude(
                Q(organization__is_banned=True) | Q(organization__is_deleted=True) | Q(organization__is_private=True) | Q(organization_id__in=blacklist))
        else:
            qs = ShopItem.objects.exclude(
                Q(organization__is_banned=True) | Q(organization__is_deleted=True) | Q(organization__is_private=True))
        if search and search[0] == '#':  # Search among posts if hashtag is used
            qs = qs.filter(is_published=True)
        elif search:
            qs = qs.filter(is_published=True, price__isnull=False)
            qs = ShopItemService.get_ordering_search_result(queryset=qs, search_word=search)
        else:
            qs = qs.filter(is_published=True, price__isnull=False).order_by('-updated_at')


        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = StartDateTimeSerializer(data=request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Validation Error'))
        self.serializer_class(context={'request': self.request})
        response = super().list(request, args, kwargs)
        start_time = serializer.validated_data['start_time']
        if start_time:
            response.data['has_new'] = ShopItemService.feed_has_new_items(timestamp=start_time)
        else:
            response.data['has_new'] = False
        return response


class OrganizationItemListView(FeedView):
    serializer_class = ItemFeedSerializer
    filter_class = FeedItemFilterWithoutOrganization
    # ordering = ['-updated_at', ]

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid organization is required in query parameters'))
        organization = serializer.validated_data['organization']
        if organization.is_deleted:
            return ShopItem.objects.none()

        qs = ShopItemService.get_organization_items_queryset_for_user(
            organization=serializer.validated_data['organization'], user=self.request.user
        ).order_by('-updated_at')
        search = self.request.GET.get('search', None)
        if search:
            qs = ShopItemService.get_ordering_search_result(queryset=qs, search_word=search)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)


class OrganizationRentalListView(ListAPIView):
    serializer_class = RentalTicketListSerializer
    filter_backends = (SearchFilter,)
    search_fields = ['name']

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid organization is required in query parameters'))
        organization = serializer.validated_data['organization']
        if organization.is_deleted:
            return ShopItem.objects.none()

        qs = ShopItemService.get_organization_rentals_queryset_for_user(
            organization=serializer.validated_data['organization'], user=self.request.user
        ).order_by('-updated_at')
        search = self.request.GET.get('search', None)
        if search:
            qs = ShopItemService.get_ordering_search_result(queryset=qs, search_word=search)
        return qs


class OrganizationTicketListView(ListAPIView):
    serializer_class = RentalTicketListSerializer
    filter_backends = (SearchFilter,)
    search_fields = ['name']

    def get_queryset(self):
        serializer = OrganizationQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid organization is required in query parameters'))
        organization = serializer.validated_data['organization']
        if organization.is_deleted:
            return ShopItem.objects.none()

        qs = ShopItemService.get_organization_tickets_queryset_for_user(
            organization=serializer.validated_data['organization'], user=self.request.user
        ).order_by('-updated_at')
        search = self.request.GET.get('search', None)
        if search:
            qs = ShopItemService.get_ordering_search_result(queryset=qs, search_word=search)
        return qs


class SubscriptionItemListView(FeedView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionItemSerializer
    # ordering = ['-updated_at', ]

    def get_queryset(self):
        qs = ShopItemService.get_items_of_subscribed_organizations(user=self.request.user).order_by('-updated_at')
        search = self.request.GET.get('search', None)
        if search:
            qs = ShopItemService.get_ordering_search_result(queryset=qs, search_word=search)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = StartDateTimeSerializer(data=request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Validation Error'))
        response = super().list(request, args, kwargs)
        start_time = serializer.validated_data['start_time']
        if start_time:
            response.data['has_new'] = ShopItemService.subscription_has_new_items(timestamp=start_time,
                                                                                  user=request.user)
        else:
            response.data['has_new'] = False
        return response


class HotlinkCollectionItemListView(ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = SubscriptionItemSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('subcategory',)

    def list(self, request, *args, **kwargs):
        hotlink = HotlinkService.get(id=self.kwargs['pk'], link_type=HOTLINK_COLLECTION)
        qs = ShopItemService.get_items_in_hotlink_collection(hotlink=hotlink)
        queryset = ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)
        queryset = self.filter_queryset(queryset)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        response.data['collection_title'] = hotlink.content

        return response
