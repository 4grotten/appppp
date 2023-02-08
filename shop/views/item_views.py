from django.db import IntegrityError
from django.db.models import Count
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, permissions
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import IntegrityException, NotAcceptableException
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from shop.filters import SuggestItemFilter, FeedItemOrderingFilter, FeedItemFilter
from shop.models import ShopItem, Complaint, RentalPeriod
from shop.permissions import CanEditItem, CanViewUnpublishedItem
from shop.serializers.item_serializers import (
    ItemCreateUpdateSerializer, ItemRentalCreateUpdateSerializer, ItemRetrieveSerializer, ItemRentalRetrieveSerializer, ItemChangePublishedSerializer, SubscriptionItemSerializer,
    ItemFeedSerializer, StartDateTimeSerializer, RentItemsPeriodSerializer
)
from shop.serializers.like_bookmark_serializers import LikeSerializer, BookmarkSerializer
from shop.serializers.other_serializers import ComplaintSerializer, SuggestItemSerializer
from shop.services.cart_services import CartItemService
from shop.services.item_services import ShopItemService
from shop.services.like_bookmark_services import LikeService, BookmarkService
from utils.translator import GoogleTranslator


class ItemCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemCreateUpdateSerializer


class ItemRentalCreateView(CreateAPIView):
    permissions = (IsAuthenticated,)
    serializer_class = ItemRentalCreateUpdateSerializer


class RentItemPeriodCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, format=None):
        try:
            rental = ShopItemService.get(id=pk)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))
        rental_period_data = {
            'rent_time_type': request.data.get('rent_time_type'),
            'start_date': request.data.get('start_date'),
            'end_date': request.data.get('end_date'),
            'start_time': request.data.get('start_time'),
            'end_time': request.data.get('end_time')
        }
        rental_period_serializer = RentItemsPeriodSerializer(data=rental_period_data)
        if rental_period_serializer.is_valid():
            rental_period = rental_period_serializer.save()
        else:
            return Response(rental_period_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        rental.rental_period = rental_period
        rental.save()
        return Response(data={'message': _('Successfully added rental period')})


class RentalPeriodRetrieveView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RentItemsPeriodSerializer
    queryset = ShopItem.objects.all()

    def retrieve(self, request, *args, **kwargs):
        rental = self.get_object()
        rental_period = rental.rental_period
        serializer = self.get_serializer(rental_period)
        return Response(serializer.data)


class ItemRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItem)
    serializer_class = ItemCreateUpdateSerializer
    queryset = ShopItem.objects.all()

    def put(self, request, *args, **kwargs):
        ShopItemService.delete_instagram_images(item_id=kwargs['pk'])
        ShopItemService.delete_instagram_video(item_id=kwargs['pk'])
        ShopItemService.change_updated_at_and_is_updated_and_removed_at_field(item_id=kwargs['pk'])
        # ShopItemService.remove_stock_if_change_subcategory(item_id=kwargs['pk'], subcategory_id=request.data['subcategory'])
        return super().put(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            self.permission_classes = (AllowAny, CanViewUnpublishedItem,)
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        if not kwargs['pk'].isdigit():
            return Response(data={
                'details': _('Not found')
            }, status=status.HTTP_404_NOT_FOUND)

        self.serializer_class = ItemRetrieveSerializer
        self.serializer_class(context={'request': self.request})
        return super().retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        CartItemService.delete_item_from_all_carts(item=ShopItem.objects.get(id=kwargs['pk']))
        return super().delete(self, request, *args, **kwargs)


class ItemRentalRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, CanEditItem)
    serializer_class = ItemRentalCreateUpdateSerializer
    queryset = ShopItem.objects.all()

    def put(self, request, *args, **kwargs):
        ShopItemService.delete_instagram_images(item_id=kwargs['pk'])
        ShopItemService.delete_instagram_video(item_id=kwargs['pk'])
        ShopItemService.change_updated_at_and_is_updated_and_removed_at_field(item_id=kwargs['pk'])
        # ShopItemService.remove_stock_if_change_subcategory(item_id=kwargs['pk'], subcategory_id=request.data['subcategory'])
        return super().put(request, *args, **kwargs)

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            self.permission_classes = (AllowAny, CanViewUnpublishedItem,)
        return super().get_permissions()

    def retrieve(self, request, *args, **kwargs):
        if not kwargs['pk'].isdigit():
            return Response(data={
                'details': _('Not found')
            }, status=status.HTTP_404_NOT_FOUND)

        self.serializer_class = ItemRentalRetrieveSerializer
        self.serializer_class(context={'request': self.request})
        return super().retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        CartItemService.delete_item_from_all_carts(item=ShopItem.objects.get(id=kwargs['pk']))
        return super().delete(self, request, *args, **kwargs)


class ItemChangePublishedStatusView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ItemChangePublishedSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ShopItemService.update_published_status(user=request.user, item=serializer.validated_data['item'],
                                                is_published=serializer.validated_data['is_published'])

        return Response(data={'message': _('Successfully updated published status')})


class LikeListCreateView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionItemSerializer

    def get_queryset(self):
        qs = ShopItemService.get_liked_items(user=self.request.user)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def post(self, request):
        serializer = LikeSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        LikeService.like_unlike_item(user=request.user, item=serializer.validated_data['item'],
                                     is_liked=serializer.validated_data['is_liked'])

        return Response(data={'message': _('Successfully updated like status')})


class BookmarkListCreateView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionItemSerializer

    def get_queryset(self):
        qs = ShopItemService.get_bookmarked_items(user=self.request.user)
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def post(self, request):
        serializer = BookmarkSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        BookmarkService.add_remove_bookmarked_item(user=request.user, item=serializer.validated_data['item'],
                                                   is_bookmarked=serializer.validated_data['is_bookmarked'])

        return Response(data={'message': _('Successfully updated bookmark status')})


class ComplaintCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Complaint.objects.all()
    serializer_class = ComplaintSerializer

    def perform_create(self, serializer):
        try:
            super().perform_create(serializer)
        except IntegrityError:
            raise IntegrityException(_('You have already complained about this item'))


class PartnerShopItemsListView(ListAPIView):
    serializer_class = ItemFeedSerializer
    filter_backends = (DjangoFilterBackend, FeedItemOrderingFilter, SearchFilter,)
    filterset_fields = ('subcategory', 'subcategory__category', 'organization__country', 'organization__city',)
    ordering_fields = ['updated_at', 'price']
    search_fields = ('article', 'id', 'name', 'description',)
    filter_class = FeedItemFilter

    def get_queryset(self):
        search = self.request.GET.get('search', None)
        partner = OrganizationService.get(id=self.kwargs['pk'])
        partners = partner.requested_partnerships.filter(is_accepted=True).values_list('accepted_by', flat=True).distinct()
        partner_organizations = Organization.objects.filter(Q(id__in=partners) | Q(id=self.kwargs['pk']))
        qs = ShopItem.objects.exclude(
            Q(organization__is_banned=True) | Q(organization__is_deleted=True) | Q(organization__is_private=True))
        if search and search[0] == '#':
            qs = qs.filter(organization__in=partner_organizations, is_published=True, price__isnull=False)
        elif search:
            qs = qs.filter(organization__in=partner_organizations, is_published=True, price__isnull=False)
            qs = ShopItemService.get_ordering_search_result(queryset=qs, search_word=search)
        else:
            qs = qs.filter(organization__in=partner_organizations, is_published=True, price__isnull=False).order_by('-updated_at')
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def list(self, request, *args, **kwargs):
        serializer = StartDateTimeSerializer(data=request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Validation Error'))
        self.serializer_class(context={'request': self.request})
        response = super().list(self, request, *args, **kwargs)
        start_time = serializer.validated_data['start_time']
        if start_time:
            response.data['has_new'] = ShopItemService.feed_has_new_items(timestamp=start_time)
        else:
            response.data['has_new'] = False
        return response


class TranslateItemTextView(GenericAPIView):

    def post(self, request):
        data = request.data
        query_lang = self.request.query_params.get('lang')
        lang = request.META.get('HTTP_ACCEPT_LANGUAGE', None)
        if query_lang:
            lang = query_lang
        body = {}
        try:
            if data['title']:
                translate_name = GoogleTranslator().translate(data['title'], lang)
                body['title'] = translate_name.text
            else:
                body['title'] = None
            if data['description']:
                translate_description = GoogleTranslator().translate(data['description'], lang)
                body['description'] = translate_description.text
            else:
                body['description'] = None
            return Response(data=body, status=status.HTTP_200_OK)
        except KeyError as e:
            error = str(e)
            return Response(data={
                "message": _("Invalid input"),
                'This field is required': error
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

class SuggestSearchItem(ListAPIView):
    serializer_class = SuggestItemSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter,)
    filterset_fields = ('organization__country',)
    search_fields = ('^name',)
    filter_class = SuggestItemFilter

    def get_queryset(self):
        qs = ShopItem.objects.filter(
            Q(is_published=True) &
            Q(organization__is_private=False) &
            Q(price__isnull=False) &
            Q(organization__is_banned=False) &
            Q(organization__is_deleted=False)
        )
        return qs

    def list(self, request, *args, **kwargs):

        search = self.request.GET['suggest_items']
        mutable = request.query_params._mutable
        request.query_params._mutable = True
        request.GET['search'] = search
        del request.GET['suggest_items']
        request.query_params._mutable = mutable

        response = super().list(request, args, kwargs)
        response = ShopItemService.get_suggest_items(response)

        return response
