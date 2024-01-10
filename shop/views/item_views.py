import calendar

from django.db import IntegrityError
from datetime import datetime
from django.db import models
from django.db.models.query_utils import Q
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, permissions
from rest_framework.filters import SearchFilter
from rest_framework.generics import CreateAPIView, RetrieveUpdateDestroyAPIView, GenericAPIView, ListAPIView, \
    RetrieveAPIView, ListCreateAPIView
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import IntegrityException, NotAcceptableException, ObjectNotFoundException
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from shop.filters import SuggestItemFilter, FeedItemOrderingFilter, FeedItemFilter
from shop.models import ShopItem, Complaint, Booking, ItemCollection, ItemBookmark, ResumeInfo, ResumeInfoFile, \
    Education
from shop.permissions import CanEditItem, CanViewUnpublishedItem
from shop.serializers.item_serializers import (
    ItemCreateUpdateSerializer, ItemRetrieveSerializer, ItemRentalRetrieveSerializer, ItemChangePublishedSerializer,
    SubscriptionItemSerializer,
    ItemFeedSerializer, StartDateTimeSerializer, RentItemsPeriodSerializer, ItemRentalYearSerializer,
    BookInfoSerializer,
    BookInfoWithUTCSerializer, ItemRentalMonthSerializer, ItemRentalDaySerializer, ItemRentalHourSerializer,
    ItemRentalMinuteSerializer, TicketPeriodSerializer, ResumeInfoUpdateSerializer, ResumeInfoFileSerializer,
    ResumePhoneNumberUpdateSerializer, ResumePhoneNumberSerializer, ResumeSocialNetworkUpdateSerializer,
    ResumeSocialNetworkSerializer, ResumeDetailInfoUpdateSerializer, ResumeDetailInfoSerializer,
    ResumeWorkExperienceSerializer, ResumeWorkExperienceUpdateSerializer, ResumeInfoSerializer,
    EducationSerializer, ResumeEducationSerializer, ResumeEducationUpdateSerializer
)
from shop.services.resume_services import ResumeInfoService, ResumePhoneNumberService, ResumeSocialNetworkService, \
    ResumeDetailInfoService, ResumeWorkExperienceService, ResumeEducationService
from transactions.serializers.transaction_serializers import BookingTransactionWithClientSerializer
from shop.serializers.like_bookmark_serializers import LikeSerializer, BookmarkSerializer, ItemCollectionSerializer, \
    ItemCollectionCreateSerializer, AddRemoveItemCollectionSerializer, ItemCollectionDetailUpdateSerializer, \
    ItemBookmarkBulkDeleteSerializer
from shop.serializers.other_serializers import ComplaintSerializer, SuggestItemSerializer
from shop.services.cart_services import CartItemService
from shop.services.item_services import ShopItemService
from shop.services.like_bookmark_services import LikeService, BookmarkService, CollectionService
from shop.services.booking_services import BookingService
from utils.translator import GoogleTranslator


class ItemCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemCreateUpdateSerializer


class ItemRentalCreateView(CreateAPIView):
    permissions = (IsAuthenticated,)
    serializer_class = ItemCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(purchase_type='rent')

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ItemTicketCreateView(CreateAPIView):
    permissions = (IsAuthenticated,)
    serializer_class = ItemCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(purchase_type=ShopItem.TICKET)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ItemResumeCreateView(CreateAPIView):
    permissions = (IsAuthenticated,)
    serializer_class = ItemCreateUpdateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(purchase_type=ShopItem.RESUME)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ResumeInfoFileCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)
    serializer_class = ResumeInfoFileSerializer
    queryset = ResumeInfoFile.objects.all()


class ResumeDetailInfoRetrieveAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        detail_info = ResumeDetailInfoService.get_detail_info_of_resume(item=kwargs['pk'])
        data = ResumeDetailInfoSerializer(detail_info).data
        return Response(data)


class ResumeInfoUpdateView(APIView):
    permissions = (IsAuthenticated,)
    serializer_class = ResumeInfoUpdateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ResumeInfoService.update_resume_info(item=serializer.validated_data['item'],
                                             gender=serializer.validated_data.get('gender'),
                                             full_name=serializer.validated_data.get('full_name'),
                                             date_of_birth=serializer.validated_data.get('date_of_birth'),
                                             languages=serializer.validated_data.get('languages'),
                                             files=serializer.validated_data.get('files', []))

        return Response(data={'message': _('Successfully updated resume info')})


class ResumePhonesListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        numbers = ResumePhoneNumberService.get_numbers_of_resume(item=kwargs['pk'])
        data = ResumePhoneNumberSerializer(numbers, many=True).data
        return Response(data)


class ResumePhoneNumberUpdateView(APIView):
    permissions = (IsAuthenticated,)
    serializer_class = ResumePhoneNumberUpdateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ResumePhoneNumberService.update_resume_phone_numbers(item=serializer.validated_data['item'],
                                                             numbers=serializer.validated_data['phone_numbers'])

        return Response(data={'message': _('Successfully updated phone numbers')})


class ResumeSocialNetworksListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        networks = ResumeSocialNetworkService.get_networks_of_resume(item=kwargs['pk'])
        data = ResumeSocialNetworkSerializer(networks, many=True).data
        return Response(data)


class ResumeSocialNetworksUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ResumeSocialNetworkUpdateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ResumeSocialNetworkService.update_resume_social_networks(item=serializer.validated_data['item'],
                                                                 urls=serializer.validated_data['urls'])

        return Response(data={'message': _('Successfully updated social networks')})


class ResumeInfoRetrieveAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        detail_info = ResumeInfoService.get_info_of_resume(item=kwargs['pk'])
        data = ResumeInfoSerializer(detail_info).data
        return Response(data)


class ResumeDetailInfoUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ResumeDetailInfoUpdateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ResumeDetailInfoService.update_resume_detail_info(item=serializer.validated_data['item'],
                                                          text=serializer.validated_data['text'])

        return Response(data={'message': _('Successfully updated detail info')})


class ResumeWorkExperienceListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        work_experiences = ResumeWorkExperienceService.get_work_experiences_of_resume(item=kwargs['pk'])
        data = ResumeWorkExperienceSerializer(work_experiences, many=True).data
        return Response(data)


class ResumeWorkExperienceUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ResumeWorkExperienceUpdateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ResumeWorkExperienceService.create_resume_work_experience(
            item=serializer.validated_data['item'], work_experiences=serializer.validated_data['work_experiences'])

        return Response(data={'message': _('Successfully updated work experiences')})


class ResumeEducationListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        educations = ResumeEducationService.get_educations_of_resume(item=kwargs['pk'])
        data = ResumeEducationSerializer(educations, many=True).data
        return Response(data)


class ResumeEducationUpdateView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ResumeEducationUpdateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        ResumeEducationService.create_resume_education(
            item=serializer.validated_data['item'], educations=serializer.validated_data['educations'])

        return Response(data={'message': _('Successfully updated educations')})




class EducationListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = EducationSerializer
    queryset = Education.objects.all()


class TicketPeriodCreateView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk, format=None):
        ticket = ShopItemService.get(id=pk)
        ticket_period_data = {
            'start_date': request.data.get('start_date'),
            'end_date': request.data.get('end_date'),
            'start_time': request.data.get('start_time'),
            'end_time': request.data.get('end_time')
        }
        ticket_period_serializer = TicketPeriodSerializer(data=ticket_period_data)
        if ticket_period_serializer.is_valid():
            ticket_period = ticket_period_serializer.save()
        else:
            return Response(ticket_period_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        ticket.ticket_period = ticket_period
        ticket.save()
        return Response(data={'message': _('Successfully added ticket period')})


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

        CollectionService.remove_from_all_collections(
            user=request.user, item=serializer.validated_data['item'],
            is_bookmarked=serializer.validated_data['is_bookmarked'])

        return Response(data={'message': _('Successfully updated bookmark status')})


class ItemBookmarkBulkDeleteView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = ItemBookmarkBulkDeleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        item_ids = serializer.validated_data.get('items', [])
        user = request.user

        ItemBookmark.objects.filter(user=user, item__in=item_ids).delete()

        collections = ItemCollection.objects.filter(user=user)
        for collection in collections:
            collection.items.remove(*item_ids)

            CollectionService.set_image_to_null_if_collection_has_no_items(collection=collection)

        return Response(data={'message': _('Items deleted successfully.')})


class CollectionsListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemCollectionSerializer

    def get_queryset(self):
        queryset = ItemCollection.objects.filter(user=self.request.user)
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query))
        queryset = queryset.order_by('-updated_at')
        return queryset

    def post(self, request, *args, **kwargs):
        serializer = ItemCollectionCreateSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        CollectionService.create_collection(
            name=serializer.validated_data['name'],
            user=request.user,
            items=[serializer.validated_data['items']]
        )
        is_bookmarked = True
        BookmarkService.add_remove_bookmarked_item(user=request.user, item=serializer.validated_data['items'],
                                                   is_bookmarked=is_bookmarked)

        return Response(data={'message': _('Successfully added to collection')})


class AddRemoveListItemCollectionView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SubscriptionItemSerializer

    def get_queryset(self):
        qs = CollectionService.get_bookmarked_items_in_collection(user=self.request.user,
                                                                  collection_id=self.kwargs['pk'])
        return ShopItemService.annotate_likes_and_bookmarks(queryset=qs, user=self.request.user)

    def post(self, request, *args, **kwargs):
        serializer = AddRemoveItemCollectionSerializer(data=self.request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        is_bookmarked = serializer.validated_data['is_bookmarked']
        CollectionService.add_remove_bookmarked_item_collection(
            collection_id=kwargs['pk'], user=request.user, item=serializer.validated_data['items'],
            is_bookmarked=is_bookmarked)

        if is_bookmarked:
            BookmarkService.add_remove_bookmarked_item(user=request.user, item=serializer.validated_data['items'],
                                                       is_bookmarked=is_bookmarked)

        return Response(data={'message': _('Successfully updated collection')})


class CollectionRetrieveUpdateDestroyView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ItemCollectionSerializer

    def get_queryset(self):
        return ItemCollection.objects.filter(user=self.request.user)

    def put(self, request, *args, **kwargs):
        serializer = ItemCollectionDetailUpdateSerializer(instance=self.get_object(), data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        collection = CollectionService.update_collection(
            collection=self.get_object(),
            name=serializer.validated_data.get('name'),
            item_id=serializer.validated_data.get('item_id'),
            items=serializer.validated_data.get('items')
        )

        serialized_collection = ItemCollectionSerializer(collection, context={'request': request}).data
        return Response(serialized_collection)

    def perform_destroy(self, instance):
        instance.delete()


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
            for _ in range(10):
                if data.get('title'):
                    translate_name = GoogleTranslator().translate(data['title'], lang)
                    if isinstance(translate_name, str):
                        continue  # Skip this iteration and try again
                    else:
                        body['title'] = translate_name.text
                        break  # Exit the loop if translation is successful
                else:
                    body['title'] = None

            for _ in range(10):
                if data.get('description'):
                    translate_description = GoogleTranslator().translate(data['description'], lang)
                    if isinstance(translate_description, str):
                        continue  # Skip this iteration and try again
                    else:
                        body['description'] = translate_description.text
                        break  # Exit the loop if translation is successful
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


class GetYearsView(ListAPIView):
    serializer_class = ItemRentalYearSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        pk = self.kwargs.get('pk')
        rental = ShopItem.objects.filter(pk=pk).first()
        context['rental'] = rental
        return context

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        shop_item = ShopItem.objects.filter(pk=pk).first()
        if shop_item is None:
            return []
        rental_period = shop_item.rental_period
        if rental_period is None:
            return []
        start_year = rental_period.start_date.year
        end_year = rental_period.end_date.year
        queryset = [{'value': str(year), 'is_booked': False, 'is_available':True} for year in range(start_year, end_year + 1)]
        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(data=queryset, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class GetMonthsView(ListAPIView):
    serializer_class = ItemRentalMonthSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        pk = self.kwargs.get('pk')
        rental = ShopItem.objects.filter(pk=pk).first()
        context['rental'] = rental
        context['time_query'] = self.request.query_params.get('time')
        return context

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        shop_item = ShopItem.objects.filter(pk=pk).first()
        if shop_item is None:
            return []

        timestamp = self.request.query_params.get('time')
        if not timestamp:
            return []

        try:
            time_datetime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M')
        except ValueError:
            return []

        year = time_datetime.year

        months = [datetime(year, month, 1).date() for month in range(1, 13)]

        queryset = []
        for month in months:
            queryset.append({
                'value': month.strftime('%Y-%m-%dT%H:%M'),
                'is_booked': False,
                'is_available': True
            })

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(data=queryset, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

class GetDaysView(ListAPIView):
    serializer_class = ItemRentalDaySerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        pk = self.kwargs.get('pk')
        rental = ShopItem.objects.filter(pk=pk).first()
        context['rental'] = rental
        context['time_query'] = self.request.query_params.get('time')
        return context

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        shop_item = ShopItem.objects.filter(pk=pk).first()
        if shop_item is None:
            return []

        timestamp = self.request.query_params.get('time')
        if not timestamp:
            return []

        try:
            time_datetime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M')
        except ValueError:
            return []

        year = time_datetime.year
        month = time_datetime.month
        num_days = calendar.monthrange(year, month)[1]

        # Generate the list of days
        days = [datetime(year, month, day).date() for day in range(1, num_days + 1)]

        queryset = []
        for day in days:
            queryset.append({
                'value': day.strftime('%Y-%m-%d'),
                'is_booked': False,
                'is_available': True
            })

        return queryset

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(data=queryset, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class GetHoursView(ListAPIView):
    serializer_class = ItemRentalHourSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        pk = self.kwargs.get('pk')
        rental = ShopItem.objects.filter(pk=pk).first()
        context['rental'] = rental
        context['time_query'] = self.request.query_params.get('time')
        return context

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        shop_item = ShopItem.objects.filter(pk=pk).first()
        if shop_item is None:
            return []

        timestamp = self.request.query_params.get('time')
        if not timestamp:
            return []

        try:
            time_datetime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M')
        except ValueError:
            return []

        rental_period = shop_item.rental_period
        if rental_period is None:
            return []

        year = time_datetime.year
        month = time_datetime.month
        day = time_datetime.day

        hours = [{'value': datetime(year, month, day, hour), 'is_booked': False, 'is_available': True} for hour in
                    range(0, 24)]

        return hours

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(data=queryset, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class GetMinutesView(ListAPIView):
    serializer_class = ItemRentalMinuteSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        pk = self.kwargs.get('pk')
        rental = ShopItem.objects.filter(pk=pk).first()
        context['rental'] = rental
        context['time_query'] = self.request.query_params.get('time')
        return context

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        shop_item = ShopItem.objects.filter(pk=pk).first()
        if shop_item is None:
            return []

        timestamp = self.request.query_params.get('time')
        if not timestamp:
            return []

        try:
            time_datetime = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M')
        except ValueError:
            return []

        rental_period = shop_item.rental_period
        if rental_period is None:
            return []

        year = time_datetime.year
        month = time_datetime.month
        day = time_datetime.day
        hour = time_datetime.hour

        minutes = [{'value': datetime(year, month, day, hour, minute), 'is_booked': False, 'is_available': True} for minute in
                    range(0, 60)]

        return minutes

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(data=queryset, many=True)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class BookRentalView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        serializer = BookInfoSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        rental = ShopItem.objects.get(id=pk)
        start_time = serializer.validated_data.get('start_time')
        end_time = serializer.validated_data.get('end_time')
        booking = Booking.objects.create(user=request.user,
                                         item=rental,
                                         organization=serializer.validated_data.get('organization', None),
                                         start_time=start_time,
                                         end_time=end_time
                                         )

        booking_process = BookingService.process_booking(user=request.user, booking_id=booking.id)

        return Response(
            {
                "message": _("Success"),
                "transaction_id": booking_process.transaction_id
            }
        )


class BookingAnonymousCheckoutView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingTransactionWithClientSerializer

    def post(self, request, pk):
        serializer = BookInfoWithUTCSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        rental = ShopItem.objects.get(id=pk)
        start_time = serializer.validated_data.get('start_time')
        end_time = serializer.validated_data.get('end_time')
        booking = Booking.objects.create(user=request.user,
                                         item=rental,
                                         organization=serializer.validated_data.get('organization', None),
                                         start_time=start_time,
                                         end_time=end_time
                                         )
        transaction = BookingService.checkout_booking_for_anonymous_client(
            request=request, employee=request.user, booking_id=booking.id,
            utc_offset_minutes=serializer.validated_data['utc_offset_minutes']
        )
        data = self.serializer_class(transaction, context={'request': request}).data
        return Response(data)