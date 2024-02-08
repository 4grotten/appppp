import calendar

from django.db import IntegrityError
from datetime import datetime
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

from django.utils.translation import activate
from common.exceptions import IntegrityException, NotAcceptableException, ObjectNotFoundException
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from shop.filters import SuggestItemFilter, FeedItemOrderingFilter, FeedItemFilter
from shop.models import ShopItem, Complaint, Booking, ItemCollection, ItemBookmark, ResumeInfoFile, \
    Education, ResumeRequest, ItemCategory, ItemSubcategory
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
    EducationSerializer, ResumeEducationSerializer, ResumeEducationUpdateSerializer, SubmitUserResumeRequestSerializer,
    AcceptDeclineUserResumeRequestSerializer, UserResumeRequestSerializer, UserResumeRequestAcceptedSerializer,
    SubmitOrganizationResumeRequestSerializer, OrganizationResumeRequestSerializer,
    OrganizationResumeRequestAcceptedSerializer, UserItemCreateUpdateSerializer, ResumeItemRetrieveSerializer,
    ResumeFilterQuaryParamsSerializer, ResumeFeedSerializer
)
from shop.services.resume_services import ResumeInfoService, ResumePhoneNumberService, ResumeSocialNetworkService, \
    ResumeDetailInfoService, ResumeWorkExperienceService, ResumeEducationService, ResumeRequestService
from transactions.serializers.transaction_serializers import BookingTransactionWithClientSerializer
from shop.serializers.like_bookmark_serializers import LikeSerializer, BookmarkSerializer, ItemCollectionSerializer, \
    ItemCollectionCreateSerializer, AddRemoveItemCollectionSerializer, ItemCollectionDetailUpdateSerializer, \
    ItemBookmarkBulkDeleteSerializer
from shop.serializers.other_serializers import ComplaintSerializer, SuggestItemSerializer
from shop.services.cart_services import CartItemService
from shop.services.item_services import ShopItemService
from shop.services.like_bookmark_services import LikeService, BookmarkService, CollectionService
from shop.services.booking_services import BookingService
from users.services import UserService
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


class ItemResumeCreateView(ListCreateAPIView):
    permissions = (IsAuthenticated,)
    serializer_class = ResumeFeedSerializer

    def get_queryset(self):
        queryset = ShopItem.objects.filter(purchase_type=ShopItem.RESUME)
        serializer = ResumeFilterQuaryParamsSerializer(data=self.request.GET)
        if not serializer.is_valid():
            raise NotAcceptableException(_('Valid quary params are required'))
        validated_data = serializer.validated_data

        category = validated_data.get('category', None)
        if category:
            queryset = queryset.filter(subcategory__category_id=category)
        subcategory = validated_data.get('subcategory', None)
        if subcategory:
            queryset = queryset.filter(subcategory_id=subcategory)

        country = validated_data.get('country', None)
        if country:
            queryset = queryset.filter(preferred_locations__contains=country)
        city = validated_data.get('city', None)
        if city:
            queryset = queryset.filter(preferred_locations__contains=city)

        salary_from = validated_data.get('salary_from', None)
        salary_to = validated_data.get('salary_to', None)
        currency = validated_data.get('currency', None)
        if salary_from:
            queryset = queryset.filter(salary_from__gte=salary_from)
        if salary_to:
            queryset = queryset.filter(salary_to__lte=salary_to)
        if currency:
            queryset = queryset.filter(currency__code=currency)
        has_work_experience = validated_data.get('has_work_experience')
        if has_work_experience:
            queryset = queryset.filter(resume_work_experience__isnull=False)
        has_education = validated_data.get('has_education')
        if has_education:
            queryset = queryset.filter(resume_education__isnull=False)

        gender = validated_data.get('gender')
        if gender:
            queryset = queryset.filter(resume_info__gender=gender)

        return queryset


    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True, context={'request': self.request})
        return Response(serializer.data)



    def create(self, request, *args, **kwargs):
        if 'organization' in request.data:
            serializer = ItemCreateUpdateSerializer(data=request.data, context={'request': request})
        elif 'user' in request.data:
            serializer = UserItemCreateUpdateSerializer(data=request.data, context={'request': request})
        else:
            return Response({'error': 'Invalid request'}, status=status.HTTP_400_BAD_REQUEST)
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
        detail_info = ResumeInfoService.get_info_of_resume(item_id=kwargs['pk'])
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


class UserResumeRequestRetrieveView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return ResumeRequestService.get(id=self.kwargs['pk'])

    def get_serializer_class(self):
        status = self.get_object().status

        if status in [ResumeRequest.IN_PROGRESS, ResumeRequest.REJECTED]:
            return UserResumeRequestSerializer
        elif status == ResumeRequest.ACCEPTED:
            return UserResumeRequestAcceptedSerializer
        return UserResumeRequestSerializer


class OrganizationResumeRequestRetrieveView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        return ResumeRequestService.get(id=self.kwargs['pk'])

    def get_serializer_class(self):
        status = self.get_object().status

        if status in [ResumeRequest.IN_PROGRESS, ResumeRequest.REJECTED]:
            return OrganizationResumeRequestSerializer
        elif status == ResumeRequest.ACCEPTED:
            return OrganizationResumeRequestAcceptedSerializer
        return OrganizationResumeRequestSerializer


class SubmitResumeRequestView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = SubmitUserResumeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        sender_user = serializer.validated_data['sender_user']
        organization = serializer.validated_data['organization']
        item = serializer.validated_data['item']
        show_contacts = serializer.validated_data['show_contacts']
        phone_numbers = serializer.validated_data['phone_numbers']
        links = serializer.validated_data['links']
        text = serializer.validated_data.get('text')
        ResumeRequestService.process_user_resume_request(sender_user=sender_user, organization=organization,
                                                         item=item, show_contacts=show_contacts,
                                                         phone_numbers=phone_numbers, links=links, text=text)

        return Response(data={'message': _('Successfully submit resume request')}, status=status.HTTP_200_OK)


class OrganizationSubmitResumeRequestView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = SubmitOrganizationResumeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        sender_organization = serializer.validated_data['sender_organization']
        organization = serializer.validated_data['organization']
        item = serializer.validated_data['item']
        show_contacts = serializer.validated_data['show_contacts']
        phone_numbers = serializer.validated_data['phone_numbers']
        links = serializer.validated_data['links']
        text = serializer.validated_data.get('text')
        ResumeRequestService.process_organization_resume_request(user=request.user,
                                                                 sender_organization=sender_organization,
                                                                 organization=organization, item=item,
                                                                 show_contacts=show_contacts,
                                                                 phone_numbers=phone_numbers,
                                                                 links=links, text=text)

        return Response(data={'message': _('Successfully submit resume request')}, status=status.HTTP_200_OK)


class AcceptResumeRequestView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = AcceptDeclineUserResumeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        resume_request_id = serializer.validated_data['resume_request_id']

        ResumeRequestService.accept_user_resume_request(resume_request_id=resume_request_id, processed_by=request.user)

        return Response(data={'message': _('Successfully accepted resume request')}, status=status.HTTP_200_OK)


class DeclineResumeRequestView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = AcceptDeclineUserResumeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        resume_request_id = serializer.validated_data['resume_request_id']

        ResumeRequestService.decline_user_resume_request(resume_request_id=resume_request_id, processed_by=request.user)

        return Response(data={'message': _('Successfully declined resume request')}, status=status.HTTP_200_OK)


class OrganizationAcceptResumeRequestView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = AcceptDeclineUserResumeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        resume_request_id = serializer.validated_data['resume_request_id']

        ResumeRequestService.accept_organization_resume_request(resume_request_id=resume_request_id, processed_by=request.user)

        return Response(data={'message': _('Successfully accepted resume request')}, status=status.HTTP_200_OK)


class OrganizationDeclineResumeRequestView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = AcceptDeclineUserResumeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        resume_request_id = serializer.validated_data['resume_request_id']

        ResumeRequestService.decline_organization_resume_request(resume_request_id=resume_request_id, processed_by=request.user)

        return Response(data={'message': _('Successfully declined resume request')}, status=status.HTTP_200_OK)


class UserResumesView(ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        items = ShopItemService.get_user_resumes(user=request.user)
        data = ResumeItemRetrieveSerializer(items, many=True, context={'request': request}).data
        return Response(data)


class CreateNewItemCategory(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # packer~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        packer = ItemCategory.objects.create(name_ru="Упаковщик", name_en='Packer', name_tr='Paketleme işçisi',
                                           name_de='Verpacker', name_zh='包装工', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=packer, name_ru="Упаковщик", name_en='Packer',
                                       name_tr='Paketleme işçisi', name_de='Verpacker', name_zh='包装工')

        ItemSubcategory.objects.create(category=packer, name_ru="Укладчик-упаковщик", name_en='Packer-Verpacker',
                                       name_tr='Paketleme işçisi', name_de='Verpacker-Packager', name_zh='包装工')

        ItemSubcategory.objects.create(category=packer, name_ru="Сборщик-упаковщик", name_en='Assembler-Packer',
                                       name_tr='Toplayıcı-Paketleme işçisi', name_de='Monteur-Verpacker',
                                       name_zh='装配工-包装工')

        ItemSubcategory.objects.create(category=packer, name_ru="Укладчик-упаковщик мороженого",
                                       name_en='Ice Cream Packer-Stacker', name_tr='Dondurma Paketleyici-İstifçi',
                                       name_de='Eisverpacker-Stapler', name_zh='冰淇淋包装工-堆垛工')

        ItemSubcategory.objects.create(category=packer, name_ru="Упаковщик мебели", name_en='Furniture Packer',
                                       name_tr='Mobilya Paketleyici', name_de='Möbelverpacker', name_zh='家具包装工')


        # promoter~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        promoter = ItemCategory.objects.create(name_ru="Промоутер", name_en='Promoter', name_tr='Promotör',
                                               name_de='Promoter', name_zh='促销员', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=promoter, name_ru="Промоутер", name_en='Promoter',
                                       name_tr='Promotör', name_de='Promoter', name_zh='促销员')

        ItemSubcategory.objects.create(category=promoter, name_ru="Промоутер-консультант",
                                       name_en='Consultant Promoter',
                                       name_tr='Danışman Promotör', name_de='Berater-Promoter', name_zh='顾问促销员')

        ItemSubcategory.objects.create(category=promoter, name_ru="Промоутер-распространитель",
                                       name_en='Distributor Promoter',
                                       name_tr='Dağıtıcı Promotör', name_de='Verteiler-Promoter', name_zh='分销促销员')

        ItemSubcategory.objects.create(category=promoter, name_ru="Супервайзер промоутеров",
                                       name_en='Promoter Supervisor',
                                       name_tr='Promotör Denetçisi', name_de='Supervisor-Promoter', name_zh='促销员监督员')

        # doctor~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        doctor = ItemCategory.objects.create(name_ru="Врач", name_en='Doctor', name_tr='Doktor',
                                             name_de='Arzt', name_zh='医生', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=doctor, name_ru="Ветеринарный врач", name_en='Veterinarian',
                                       name_tr='Veteriner Hekim', name_de='Tierarzt', name_zh='兽医')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-терапевт", name_en='General Practitioner',
                                       name_tr='Genel Pratisyen', name_de='Allgemeinmediziner', name_zh='全科医生')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-стоматолог", name_en='Dentist',
                                       name_tr='Diş Hekimi', name_de='Zahnarzt', name_zh='牙医')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-хирург", name_en='Surgeon',
                                       name_tr='Cerrah', name_de='Chirurg', name_zh='外科医生')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-педиатр", name_en='Pediatrician',
                                       name_tr='Pediatri Uzmanı', name_de='Kinderarzt', name_zh='儿科医生')

        ItemSubcategory.objects.create(category=doctor, name_ru="Главный врач", name_en='Chief Medical Officer',
                                       name_tr='Baş Hekim', name_de='Chefarzt', name_zh='首席医务官')

        ItemSubcategory.objects.create(category=doctor, name_ru="Санитарный врач", name_en='Sanitary Doctor',
                                       name_tr='Sağlık Görevlisi', name_de='Sanitätsarzt', name_zh='卫生医生')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-невролог", name_en='Neurologist',
                                       name_tr='Nörolog', name_de='Neurologe', name_zh='神经科医生')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач акушер-гинеколог",
                                       name_en='Obstetrician-Gynecologist',
                                       name_tr='Jinekolog-Doğum Uzmanı', name_de='Geburtshelfer-Gynäkolog',
                                       name_zh='产科医生-妇科医生')

        ItemSubcategory.objects.create(category=doctor, name_ru="Ассистент врача-стоматолога",
                                       name_en='Dental Assistant',
                                       name_tr='Diş Hekimi Asistanı', name_de='Zahnarzthelfer', name_zh='牙科助理')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-эксперт", name_en='Medical Expert',
                                       name_tr='Tıp Uzmanı', name_de='Medizinischer Experte', name_zh='医学专家')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-офтальмолог", name_en='Ophthalmologist',
                                       name_tr='Göz Doktoru', name_de='Augenarzt', name_zh='眼科医生')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-косметолог", name_en='Cosmetologist',
                                       name_tr='Kozmetolog', name_de='Kosmetiker', name_zh='美容医生')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-лаборант",
                                       name_en='Medical Laboratory Technician',
                                       name_tr='Tıbbi Laboratuvar Teknisyeni',
                                       name_de='Medizinisch-technischer Assistent', name_zh='医学实验室技术员')

        ItemSubcategory.objects.create(category=doctor, name_ru="Врач-уролог", name_en='Urologist',
                                       name_tr='Ürolog', name_de='Urologe', name_zh='泌尿科医生')

        # designer~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        designer = ItemCategory.objects.create(name_ru="Дизайнер", name_en='Designer', name_tr='Tasarımcı',
                                               name_de='Designer', name_zh='设计师', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=designer, name_ru="Дизайнер", name_en='Designer',
                                       name_tr='Tasarımcı', name_de='Designer', name_zh='设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Дизайнер интерьеров", name_en='Interior Designer',
                                       name_tr='İç Mimar', name_de='Innenarchitekt', name_zh='室内设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Дизайнер-верстальщик", name_en='Layout Designer',
                                       name_tr='Düzen Tasarımcısı', name_de='Layout Designer', name_zh='版面设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Архитектор-дизайнер", name_en='Architect-Designer',
                                       name_tr='Mimar-Tasarımcı', name_de='Architekt-Designer', name_zh='建筑师-设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Художник-дизайнер", name_en='Artist-Designer',
                                       name_tr='Sanatçı-Tasarımcı', name_de='Künstler-Designer', name_zh='艺术家-设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Дизайнер-консультант", name_en='Design Consultant',
                                       name_tr='Tasarım Danışmanı', name_de='Design Consultant', name_zh='设计顾问')

        ItemSubcategory.objects.create(category=designer, name_ru="Графический дизайнер", name_en='Graphic Designer',
                                       name_tr='Grafik Tasarımcı', name_de='Grafikdesigner', name_zh='平面设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Web-дизайнер", name_en='Web Designer',
                                       name_tr='Web Tasarımcı', name_de='Webdesigner', name_zh='网页设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Дизайнер-художник", name_en='Designer-Artist',
                                       name_tr='Tasarımcı-Sanatçı', name_de='Designer-Künstler', name_zh='设计师-艺术家')

        ItemSubcategory.objects.create(category=designer, name_ru="Помощник дизайнера", name_en='Design Assistant',
                                       name_tr='Tasarım Asistanı', name_de='Design Assistant', name_zh='设计助理')

        ItemSubcategory.objects.create(category=designer, name_ru="Веб-дизайнер", name_en='Web Designer',
                                       name_tr='Web Tasarımcı', name_de='Webdesigner', name_zh='网页设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Дизайнер одежды", name_en='Fashion Designer',
                                       name_tr='Moda Tasarımcısı', name_de='Mode Designer', name_zh='时装设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Верстальщик-дизайнер", name_en='Layout Designer',
                                       name_tr='Düzen Tasarımcısı', name_de='Layout Designer', name_zh='版面设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Ландшафтный дизайнер", name_en='Landscape Designer',
                                       name_tr='Pejzaş Tasarımcısı', name_de='Landschaftsdesigner', name_zh='景观设计师')

        ItemSubcategory.objects.create(category=designer, name_ru="Фотограф-дизайнер", name_en='Photographer-Designer',
                                       name_tr='Fotoğrafçı-Tasarımcı', name_de='Fotograf-Designer', name_zh='摄影师-设计师')

        # programmer~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        programmer = ItemCategory.objects.create(name_ru="Программист", name_en='Programmer', name_tr='Programcı',
                                                 name_de='Programmierer', name_zh='程序员',
                                                 purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист", name_en='Programmer',
                                       name_tr='Programcı', name_de='Programmierer', name_zh='程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Инженер-программист",
                                       name_en='Engineer Programmer',
                                       name_tr='Mühendis Programcı', name_de='Ingenieur-Programmierer',
                                       name_zh='工程师程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист-разработчик",
                                       name_en='Developer Programmer',
                                       name_tr='Geliştirici Programcı', name_de='Entwickler-Programmierer',
                                       name_zh='开发者程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Web-программист", name_en='Web Programmer',
                                       name_tr='Web Programcı', name_de='Web-Programmierer', name_zh='Web程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист С++", name_en='C++ Programmer',
                                       name_tr='C++ Programcı', name_de='C++-Programmierer', name_zh='C++程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="PHP-программист", name_en='PHP Programmer',
                                       name_tr='PHP Programcı', name_de='PHP-Programmierer', name_zh='PHP程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист Delphi", name_en='Delphi Programmer',
                                       name_tr='Delphi Programcı', name_de='Delphi-Programmierer', name_zh='Delphi程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист PHP", name_en='PHP Programmer',
                                       name_tr='PHP Programcı', name_de='PHP-Programmierer', name_zh='PHP程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист Java", name_en='Java Programmer',
                                       name_tr='Java Programcı', name_de='Java-Programmierer', name_zh='Java程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист-стажер", name_en='Intern Programmer',
                                       name_tr='Stajyer Programcı', name_de='Praktikant-Programmierer', name_zh='实习程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Аналитик-программист",
                                       name_en='Analyst Programmer',
                                       name_tr='Analist Programcı', name_de='Analytiker-Programmierer', name_zh='分析程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Техник-программист",
                                       name_en='Technician Programmer',
                                       name_tr='Tekniker Programcı', name_de='Techniker-Programmierer',
                                       name_zh='技术员程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист 1C", name_en='1C Programmer',
                                       name_tr='1C Programcı', name_de='1C-Programmierer', name_zh='1C程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист Oracle", name_en='Oracle Programmer',
                                       name_tr='Oracle Programcı', name_de='Oracle-Programmierer', name_zh='Oracle程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист IOS", name_en='iOS Programmer',
                                       name_tr='iOS Programcı', name_de='iOS-Programmierer', name_zh='iOS程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист Android", name_en='Android Programmer',
                                       name_tr='Android Programcı', name_de='Android-Programmierer',
                                       name_zh='Android程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист Backend", name_en='Backend Programmer',
                                       name_tr='Backend Programcı', name_de='Backend-Programmierer', name_zh='后端程序员')

        ItemSubcategory.objects.create(category=programmer, name_ru="Программист Frontend",
                                       name_en='Frontend Programmer',
                                       name_tr='Frontend Programcı', name_de='Frontend-Programmierer', name_zh='前端程序员')

        # trade_representative~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        trade_representative = ItemCategory.objects.create(name_ru="Торговый представитель",
                                                           name_en='Trade Representative',
                                                           name_tr='Satış Temsilcisi', name_de='Handelsvertreter',
                                                           name_zh='销售代表',
                                                           purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=trade_representative, name_ru="Торговый представитель",
                                       name_en='Trade Representative',
                                       name_tr='Satış Temsilcisi', name_de='Handelsvertreter', name_zh='销售代表')

        ItemSubcategory.objects.create(category=trade_representative, name_ru="Региональный торговый представитель",
                                       name_en='Regional Trade Representative',
                                       name_tr='Bölgesel Satış Temsilcisi', name_de='Regionaler Handelsvertreter',
                                       name_zh='区域销售代表')

        ItemSubcategory.objects.create(category=trade_representative, name_ru="Торговый представитель отдела продаж",
                                       name_en='Sales Department Trade Representative',
                                       name_tr='Satış Departmanı Temsilcisi',
                                       name_de='Vertriebsabteilung Handelsvertreter', name_zh='销售部销售代表')

        ItemSubcategory.objects.create(category=trade_representative,
                                       name_ru="Торговый представитель по работе с ключевыми клиентами",
                                       name_en='Key Account Trade Representative',
                                       name_tr='Anahtar Hesap Satış Temsilcisi', name_de='Key Account Handelsvertreter',
                                       name_zh='主要客户销售代表')

        ItemSubcategory.objects.create(category=trade_representative,
                                       name_ru="Торговый представитель отдела прямых продаж",
                                       name_en='Direct Sales Department Trade Representative',
                                       name_tr='Doğrudan Satış Departmanı Temsilcisi',
                                       name_de='Direktvertriebsabteilung Handelsvertreter', name_zh='直销部销售代表')

        ItemSubcategory.objects.create(category=trade_representative,
                                       name_ru="Торговый представитель по ключевым клиентам",
                                       name_en='Key Clients Trade Representative',
                                       name_tr='Anahtar Müşteriler Satış Temsilcisi',
                                       name_de='Key Clients Handelsvertreter', name_zh='主要客户销售代表')

        ItemSubcategory.objects.create(category=trade_representative, name_ru="Торговый представитель прямой доставки",
                                       name_en='Direct Delivery Trade Representative',
                                       name_tr='Doğrudan Teslimat Satış Temsilcisi',
                                       name_de='Direktlieferung Handelsvertreter', name_zh='直接交付销售代表')

        ItemSubcategory.objects.create(category=trade_representative, name_ru="Торговый представитель по сетям",
                                       name_en='Network Trade Representative',
                                       name_tr='Ağ Satış Temsilcisi', name_de='Netzwerk Handelsvertreter',
                                       name_zh='网络销售代表')

        ItemSubcategory.objects.create(category=trade_representative, name_ru="Старший торговый представитель",
                                       name_en='Senior Trade Representative',
                                       name_tr='Kıdemli Satış Temsilcisi', name_de='Senior Handelsvertreter',
                                       name_zh='高级销售代表')

        ItemSubcategory.objects.create(category=trade_representative, name_ru="Торговый представитель региональный",
                                       name_en='Regional Trade Representative',
                                       name_tr='Bölgesel Satış Temsilcisi', name_de='Regionaler Handelsvertreter',
                                       name_zh='区域销售代表')

        ItemSubcategory.objects.create(category=trade_representative, name_ru="Торговый представитель сети",
                                       name_en='Network Trade Representative',
                                       name_tr='Ağ Satış Temsilcisi', name_de='Netzwerk Handelsvertreter',
                                       name_zh='网络销售代表')

        # analyst~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        analyst = ItemCategory.objects.create(name_ru="Аналитик", name_en='Analyst', name_tr='Analist',
                                              name_de='Analyst', name_zh='分析师', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=analyst, name_ru="Аналитик", name_en='Analyst',
                                       name_tr='Analist', name_de='Analyst', name_zh='分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Финансовый аналитик", name_en='Financial Analyst',
                                       name_tr='Finansal Analist', name_de='Finanzanalyst', name_zh='财务分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Экономист-аналитик", name_en='Economist Analyst',
                                       name_tr='Ekonomist Analist', name_de='Ökonom-Analyst', name_zh='经济学家分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Бизнес-аналитик", name_en='Business Analyst',
                                       name_tr='İş Analisti', name_de='Business Analyst', name_zh='业务分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Маркетолог-аналитик", name_en='Marketing Analyst',
                                       name_tr='Pazarlama Analisti', name_de='Marketing Analyst', name_zh='市场分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Системный аналитик", name_en='System Analyst',
                                       name_tr='Sistem Analisti', name_de='System Analyst', name_zh='系统分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Кредитный аналитик", name_en='Credit Analyst',
                                       name_tr='Kredi Analisti', name_de='Kreditanalyst', name_zh='信用分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Инвестиционный аналитик",
                                       name_en='Investment Analyst',
                                       name_tr='Yatırım Analisti', name_de='Investment Analyst', name_zh='投资分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Аналитик-маркетолог", name_en='Analyst Marketer',
                                       name_tr='Analiz Pazarlamacı', name_de='Analyst Marketer', name_zh='分析市场营销师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Аналитик отдела продаж",
                                       name_en='Sales Department Analyst',
                                       name_tr='Satış Departmanı Analisti', name_de='Vertriebsabteilung Analyst',
                                       name_zh='销售部分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Химик-аналитик", name_en='Chemical Analyst',
                                       name_tr='Kimya Analisti', name_de='Chemieanalyst', name_zh='化学分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Аналитик бизнес-процессов",
                                       name_en='Business Process Analyst',
                                       name_tr='İş Süreçleri Analisti', name_de='Business Process Analyst',
                                       name_zh='业务流程分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Младший аналитик", name_en='Junior Analyst',
                                       name_tr='Junior Analist', name_de='Junior Analyst', name_zh='初级分析师')

        ItemSubcategory.objects.create(category=analyst, name_ru="Ассистент аналитика", name_en='Analyst Assistant',
                                       name_tr='Analiz Asistanı', name_de='Analyst Assistant', name_zh='分析师助理')

        ItemSubcategory.objects.create(category=analyst, name_ru="Аналитик-программист", name_en='Analyst Programmer',
                                       name_tr='Analiz Programcısı', name_de='Analyst Programmer', name_zh='分析师程序员')

        # teacher~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        teacher = ItemCategory.objects.create(name_ru="Преподаватель", name_en='Teacher', name_tr='Öğretmen',
                                              name_de='Lehrer', name_zh='教师', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель английского языка",
                                       name_en='English Language Teacher',
                                       name_tr='İngilizce Öğretmen', name_de='Englischlehrer', name_zh='英语教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель", name_en='Teacher',
                                       name_tr='Öğretmen', name_de='Lehrer', name_zh='教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель немецкого языка",
                                       name_en='German Language Teacher',
                                       name_tr='Almanca Öğretmen', name_de='Deutschlehrer', name_zh='德语教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель французского языка",
                                       name_en='French Language Teacher',
                                       name_tr='Fransızca Öğretmen', name_de='Französischlehrer', name_zh='法语教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель иностранных языков",
                                       name_en='Foreign Language Teacher',
                                       name_tr='Yabancı Dil Öğretmeni', name_de='Fremdsprachenlehrer', name_zh='外语教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель русского языка и литературы",
                                       name_en='Russian Language and Literature Teacher',
                                       name_tr='Rusça ve Edebiyat Öğretmeni', name_de='Russisch- und Literaturlehrer',
                                       name_zh='俄语和文学教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Тренер-преподаватель", name_en='Coach and Teacher',
                                       name_tr='Koç ve Öğretmen', name_de='Trainer und Lehrer', name_zh='教练和教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель математики",
                                       name_en='Mathematics Teacher',
                                       name_tr='Matematik Öğretmeni', name_de='Mathematiklehrer', name_zh='数学教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель русского языка как иностранного",
                                       name_en='Russian as a Foreign Language Teacher',
                                       name_tr='Rusça Öğretmeni', name_de='Russisch als Fremdsprache Lehrer',
                                       name_zh='俄语作为外语教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель информатики",
                                       name_en='Computer Science Teacher',
                                       name_tr='Bilgisayar Bilimleri Öğretmeni', name_de='Informatiklehrer',
                                       name_zh='计算机科学教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель испанского языка",
                                       name_en='Spanish Language Teacher',
                                       name_tr='İspanyolca Öğretmen', name_de='Spanischlehrer', name_zh='西班牙语教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель экономических дисциплин",
                                       name_en='Economics Teacher',
                                       name_tr='Ekonomi Öğretmeni', name_de='Wirtschaftslehrer', name_zh='经济学教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель русского языка",
                                       name_en='Russian Language Teacher',
                                       name_tr='Rusça Öğretmeni', name_de='Russischlehrer', name_zh='俄语教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель психологии",
                                       name_en='Psychology Teacher',
                                       name_tr='Psikoloji Öğretmeni', name_de='Psychologielehrer', name_zh='心理学教师')

        ItemSubcategory.objects.create(category=teacher, name_ru="Преподаватель танцев", name_en='Dance Teacher',
                                       name_tr='Dans Öğretmeni', name_de='Tanzlehrer', name_zh='舞蹈教师')

        # installer~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        installer = ItemCategory.objects.create(name_ru="Монтажник", name_en='Installer', name_tr='Montajcı',
                                                name_de='Monteur', name_zh='安装工', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник", name_en='Installer',
                                       name_tr='Montajcı', name_de='Monteur', name_zh='安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник слаботочных систем",
                                       name_en='Low Voltage Systems Installer',
                                       name_tr='Düşük Voltaj Sistemleri Montajcısı',
                                       name_de='Niederspannungssysteme Monteur', name_zh='低压系统安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник связи", name_en='Communication Installer',
                                       name_tr='İletişim Montajcısı', name_de='Kommunikationsmonteur', name_zh='通信安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник ЛВС",
                                       name_en='Structured Cabling Systems Installer',
                                       name_tr='Yapılandırılmış Kablolama Sistemleri Montajcısı',
                                       name_de='Strukturierte Verkabelungssysteme Monteur', name_zh='结构化布线系统安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник натяжных потолков",
                                       name_en='Stretch Ceiling Installer',
                                       name_tr='Germe Tavan Montajcısı', name_de='Spanndecken Monteur',
                                       name_zh='拉伸天花板安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник кондиционеров",
                                       name_en='Air Conditioner Installer',
                                       name_tr='Klima Montajcısı', name_de='Klimaanlagen Monteur', name_zh='空调安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Инженер-монтажник", name_en='Engineer Installer',
                                       name_tr='Mühendis Montajcısı', name_de='Ingenieur Monteur', name_zh='工程师安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник СКС", name_en='SKS Installer',
                                       name_tr='SKS Montajcısı', name_de='SKS Monteur', name_zh='SKS安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник систем вентиляции и кондиционирования",
                                       name_en='Ventilation and Air Conditioning Systems Installer',
                                       name_tr='Havalandırma ve Klima Sistemleri Montajcısı',
                                       name_de='Lüftungs- und Klimaanlagensysteme Monteur', name_zh='通风和空调系统安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Бригадир монтажников",
                                       name_en='Installer Team Leader',
                                       name_tr='Montajcı Takım Lideri', name_de='Montageteamleiter', name_zh='安装工队队长')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник ОПС", name_en='OPS Installer',
                                       name_tr='OPS Montajcısı', name_de='OPS Monteur', name_zh='OPS安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Слесарь-монтажник", name_en='Locksmith Installer',
                                       name_tr='Kilitçi Montajcısı', name_de='Schlosser Monteur', name_zh='锁匠安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник радиоэлектронной аппаратуры и приборов",
                                       name_en='Radio Electronics Equipment and Instrument Installer',
                                       name_tr='Radyo Elektronik Ekipman ve Cihaz Montajcısı',
                                       name_de='Radioelektronikgeräte- und Instrumentenmonteur',
                                       name_zh='无线电电子设备和仪器安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник технологических трубопроводов",
                                       name_en='Technological Pipelines Installer',
                                       name_tr='Teknolojik Boru Hatları Montajcısı',
                                       name_de='Technologische Rohrleitungen Monteur', name_zh='技术管道安装工')

        ItemSubcategory.objects.create(category=installer, name_ru="Монтажник систем вентиляции",
                                       name_en='Ventilation Systems Installer',
                                       name_tr='Havalandırma Sistemleri Montajcısı', name_de='Lüftungssysteme Monteur',
                                       name_zh='通风系统安装工')

        # locksmith~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        locksmith = ItemCategory.objects.create(name_ru="Слесарь", name_en='Locksmith', name_tr='Cerrah',
                                                name_de='Schlosser', name_zh='锁匠', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь-сантехник", name_en='Plumbing Locksmith',
                                       name_tr='Tesisatçı Cerrah', name_de='Sanitär-Schlosser', name_zh='管道锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь", name_en='Locksmith',
                                       name_tr='Cerrah', name_de='Schlosser', name_zh='锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь-ремонтник", name_en='Repair Locksmith',
                                       name_tr='Onarım Cerrah', name_de='Reparaturschlosser', name_zh='修理锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь механосборочных работ",
                                       name_en='Mechanical Assembly Locksmith',
                                       name_tr='Mekanik Montaj Cerrah', name_de='Mechanischer Montageschlosser',
                                       name_zh='机械组装锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь по ремонту автомобилей",
                                       name_en='Automobile Repair Locksmith',
                                       name_tr='Oto Tamir Cerrah', name_de='Kfz-Reparaturschlosser', name_zh='汽车维修锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь КИПиА", name_en='C&I Locksmith',
                                       name_tr='K&A Cerrah', name_de='MSR Techniker', name_zh='仪表和自动化锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь-сборщик", name_en='Assembler Locksmith',
                                       name_tr='Montaj Cerrah', name_de='Montageschlosser', name_zh='装配锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь МСР",
                                       name_en='Instrumentation and Control Locksmith',
                                       name_tr='Ölçüm Cerrah', name_de='MSR Techniker', name_zh='仪表和自动化锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь по ремонту оборудования",
                                       name_en='Equipment Repair Locksmith',
                                       name_tr='Ekipman Onarım Cerrah', name_de='Maschinenreparaturschlosser',
                                       name_zh='设备维修锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь-монтажник",
                                       name_en='Installation Locksmith',
                                       name_tr='Montaj Cerrah', name_de='Montageschlosser', name_zh='安装锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь-инструментальщик",
                                       name_en='Toolmaker Locksmith',
                                       name_tr='Alet Yapımı Cerrah', name_de='Werkzeugmacher Schlosser',
                                       name_zh='模具制造锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь по ремонту подвижного состава",
                                       name_en='Vehicle Repair Locksmith',
                                       name_tr='Araç Tamir Cerrah', name_de='Fahrzeugreparaturschlosser',
                                       name_zh='车辆维修锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь бутыломоечной машины",
                                       name_en='Bottle Washing Machine Locksmith',
                                       name_tr='Şişe Yıkama Makinesi Cerrah', name_de='Flaschenwaschmaschine Schlosser',
                                       name_zh='瓶洗锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь дробильных установок",
                                       name_en='Crushing Plant Locksmith',
                                       name_tr='Kırma Tesisi Cerrah', name_de='Brecheranlagen Schlosser',
                                       name_zh='破碎机设备锁匠')

        ItemSubcategory.objects.create(category=locksmith, name_ru="Слесарь по КИПиА", name_en='C&I Locksmith',
                                       name_tr='K&A Cerrah', name_de='MSR Techniker', name_zh='仪表和自动化锁匠')

        # chef~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        chef = ItemCategory.objects.create(name_ru="Повар", name_en='Chef', name_tr='Şef',
                                           name_de='Koch', name_zh='厨师', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=chef, name_ru="Повар", name_en='Cook',
                                       name_tr='Aşçı', name_de='Koch', name_zh='厨师')

        ItemSubcategory.objects.create(category=chef, name_ru="Шеф-повар", name_en='Head Chef',
                                       name_tr='Baş Aşçı', name_de='Küchenchef', name_zh='主厨')

        ItemSubcategory.objects.create(category=chef, name_ru="Повар холодного цеха", name_en='Cold Kitchen Chef',
                                       name_tr='Soğuk Mutfak Aşçısı', name_de='Koch der kalten Küche', name_zh='冷菜厨师')

        ItemSubcategory.objects.create(category=chef, name_ru="Повар горячего цеха", name_en='Hot Kitchen Chef',
                                       name_tr='Sıcak Mutfak Aşçısı', name_de='Koch der warmen Küche', name_zh='热菜厨师')

        ItemSubcategory.objects.create(category=chef, name_ru="Помощник повара", name_en='Assistant Cook',
                                       name_tr='Aşçı Yardımcısı', name_de='Kochassistent', name_zh='助理厨师')

        ItemSubcategory.objects.create(category=chef, name_ru="Повар ресторана", name_en='Restaurant Chef',
                                       name_tr='Restoran Aşçısı', name_de='Restaurantkoch', name_zh='餐厅厨师')

        ItemSubcategory.objects.create(category=chef, name_ru="Повар-кондитер", name_en='Pastry Chef',
                                       name_tr='Pastacı', name_de='Konditor', name_zh='糕点师')

        ItemSubcategory.objects.create(category=chef, name_ru="Повар-сушист", name_en='Sushi Chef',
                                       name_tr='Sushi Şefi', name_de='Sushi Koch', name_zh='寿司师')

        ItemSubcategory.objects.create(category=chef, name_ru="Старший повар", name_en='Senior Chef',
                                       name_tr='Kıdemli Aşçı', name_de='Senior Koch', name_zh='高级厨师')

        ItemSubcategory.objects.create(category=chef, name_ru="Суши-повар", name_en='Sushi Chef',
                                       name_tr='Sushi Şefi', name_de='Sushi Koch', name_zh='寿司师')

        ItemSubcategory.objects.create(category=chef, name_ru="Заместитель шеф-повара", name_en='Deputy Head Chef',
                                       name_tr='Baş Aşçı Yardımcısı', name_de='Stellvertretender Küchenchef',
                                       name_zh='副主厨')

        ItemSubcategory.objects.create(category=chef, name_ru="Повар судовой", name_en="Ship's Cook",
                                       name_tr='Gemi Aşçısı', name_de='Schiffs Koch', name_zh='船上厨师')

        ItemSubcategory.objects.create(category=chef, name_ru="Повар-бригадир", name_en='Brigade Chef',
                                       name_tr='Brigat Aşçı', name_de='Brigadekoch', name_zh='团队厨师')

        ItemSubcategory.objects.create(category=chef, name_ru="Повар-технолог", name_en='Chef Technologist',
                                       name_tr='Şef Teknolog', name_de='Küchen Technologe', name_zh='主厨技术员')

        # waiter~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        waiter = ItemCategory.objects.create(name_ru="Официант", name_en='Waiter', name_tr='Garson',
                                             name_de='Kellner', name_zh='服务员', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=waiter, name_ru="Официант-бармен", name_en='Waiter-Bartender',
                                       name_tr='Garson-Barman', name_de='Kellner-Barkeeper', name_zh='服务员-调酒师')

        ItemSubcategory.objects.create(category=waiter, name_ru="Бармен-официант", name_en='Bartender-Waiter',
                                       name_tr='Barman-Garson', name_de='Barkeeper-Kellner', name_zh='调酒师-服务员')

        ItemSubcategory.objects.create(category=waiter, name_ru="Официант", name_en='Waiter',
                                       name_tr='Garson', name_de='Kellner', name_zh='服务员')

        ItemSubcategory.objects.create(category=waiter, name_ru="Старший официант", name_en='Senior Waiter',
                                       name_tr='Kıdemli Garson', name_de='Senior Kellner', name_zh='高级服务员')

        # copywriter~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        copywriter = ItemCategory.objects.create(name_ru="Копирайтер", name_en='Copywriter', name_tr='Kopya Yazarı',
                                                 name_de='Texter', name_zh='文案撰稿人', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=copywriter, name_ru="Копирайтер", name_en='Copywriter',
                                       name_tr='Kopya Yazarı', name_de='Texter', name_zh='文案撰稿人')

        ItemSubcategory.objects.create(category=copywriter, name_ru="Журналист-копирайтер",
                                       name_en='Journalist-Copywriter',
                                       name_tr='Gazeteci-Kopya Yazarı', name_de='Journalist-Texter', name_zh='记者文案撰稿人')

        ItemSubcategory.objects.create(category=copywriter, name_ru="Дизайнер-копирайтер",
                                       name_en='Designer-Copywriter',
                                       name_tr='Tasarımcı-Kopya Yazarı', name_de='Designer-Texter', name_zh='设计师文案撰稿人')

        # intern~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        intern = ItemCategory.objects.create(name_ru="Стажер", name_en='Intern', name_tr='Stajyer',
                                             name_de='Praktikant', name_zh='实习生', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер отдела маркетинга",
                                       name_en='Marketing Department Intern',
                                       name_tr='Pazarlama Departmanı Stajyeri', name_de='Marketingabteilung Praktikant',
                                       name_zh='市场部实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Программист-стажер", name_en='Programming Intern',
                                       name_tr='Programlama Stajyeri', name_de='Programmierpraktikant', name_zh='编程实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер в отделе маркетинга",
                                       name_en='Marketing Department Intern',
                                       name_tr='Pazarlama Departmanı Stajyeri', name_de='Marketingabteilung Praktikant',
                                       name_zh='市场部实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер-аналитик", name_en='Analyst Intern',
                                       name_tr='Analiz Stajyeri', name_de='Analyst Praktikant', name_zh='分析实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер SAP", name_en='SAP Intern',
                                       name_tr='SAP Stajyeri', name_de='SAP Praktikant', name_zh='SAP实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер в отдел маркетинга",
                                       name_en='Marketing Department Intern',
                                       name_tr='Pazarlama Departmanı Stajyeri', name_de='Marketingabteilung Praktikant',
                                       name_zh='市场部实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Аналитик-стажер", name_en='Analyst Intern',
                                       name_tr='Analiz Stajyeri', name_de='Analyst Praktikant', name_zh='分析实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер-программист", name_en='Programming Intern',
                                       name_tr='Programlama Stajyeri', name_de='Programmierpraktikant', name_zh='编程实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер в финансовый отдел",
                                       name_en='Finance Department Intern',
                                       name_tr='Maliye Departmanı Stajyeri', name_de='Finanzabteilung Praktikant',
                                       name_zh='财务部实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер в банк", name_en='Bank Intern',
                                       name_tr='Banka Stajyeri', name_de='Bankpraktikant', name_zh='银行实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер финансового отдела",
                                       name_en='Finance Department Intern',
                                       name_tr='Maliye Departmanı Stajyeri', name_de='Finanzabteilung Praktikant',
                                       name_zh='财务部实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер-разработчик", name_en='Development Intern',
                                       name_tr='Geliştirme Stajyeri', name_de='Entwicklungspraktikant', name_zh='开发实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер в рекламное агентство",
                                       name_en='Advertising Agency Intern',
                                       name_tr='Reklam Ajansı Stajyeri', name_de='Werbung Agentur Praktikant',
                                       name_zh='广告公司实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер в отдел персонала",
                                       name_en='Human Resources Intern',
                                       name_tr='İnsan Kaynakları Stajyeri', name_de='Personalabteilung Praktikant',
                                       name_zh='人力资源部实习生')

        ItemSubcategory.objects.create(category=intern, name_ru="Стажер адвоката", name_en='Legal Intern',
                                       name_tr='Hukuk Stajyeri', name_de='Rechtsanwaltspraktikant', name_zh='法律实习生')

        # director~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        director = ItemCategory.objects.create(name_ru="Директор", name_en='Director', name_tr='Direktör',
                                               name_de='Direktor', name_zh='总监', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=director, name_ru="Директор филиала", name_en='Branch Director',
                                       name_tr='Şube Direktörü', name_de='Filialdirektor', name_zh='分公司总监')

        ItemSubcategory.objects.create(category=director, name_ru="Коммерческий директор",
                                       name_en='Commercial Director',
                                       name_tr='Ticaret Direktörü', name_de='Handelsdirektor', name_zh='商务总监')

        ItemSubcategory.objects.create(category=director, name_ru="Директор магазина", name_en='Store Director',
                                       name_tr='Mağaza Direktörü', name_de='Ladenleiter', name_zh='商店总监')

        ItemSubcategory.objects.create(category=director, name_ru="Директор по продажам", name_en='Sales Director',
                                       name_tr='Satış Direktörü', name_de='Vertriebsleiter', name_zh='销售总监')

        ItemSubcategory.objects.create(category=director, name_ru="Директор по персоналу", name_en='HR Director',
                                       name_tr='İnsan Kaynakları Direktörü', name_de='Personalleiter', name_zh='人力资源总监')

        ItemSubcategory.objects.create(category=director, name_ru="Технический директор", name_en='Technical Director',
                                       name_tr='Teknik Direktör', name_de='Technischer Direktor', name_zh='技术总监')

        ItemSubcategory.objects.create(category=director, name_ru="Арт-директор", name_en='Art Director',
                                       name_tr='Sanat Direktörü', name_de='Art Director', name_zh='艺术总监')

        ItemSubcategory.objects.create(category=director, name_ru="Директор по маркетингу",
                                       name_en='Marketing Director',
                                       name_tr='Pazarlama Direktörü', name_de='Marketing Direktor', name_zh='市场总监')

        ItemSubcategory.objects.create(category=director, name_ru="Административный директор",
                                       name_en='Administrative Director',
                                       name_tr='Yönetim Direktörü', name_de='Verwaltungsdirektor', name_zh='行政总监')

        ItemSubcategory.objects.create(category=director, name_ru="Заместитель финансового директора",
                                       name_en='Deputy Finance Director',
                                       name_tr='Maliye Direktörü Yardımcısı',
                                       name_de='Stellvertretender Finanzdirektor', name_zh='财务总监助理')

        ItemSubcategory.objects.create(category=director, name_ru="Заместитель генерального директора",
                                       name_en='Deputy General Director',
                                       name_tr='Genel Direktör Yardımcısı', name_de='Stellvertretender Generaldirektor',
                                       name_zh='总经理助理')

        ItemSubcategory.objects.create(category=director, name_ru="Директор по логистике", name_en='Logistics Director',
                                       name_tr='Lojistik Direktörü', name_de='Logistik Direktor', name_zh='物流总监')

        ItemSubcategory.objects.create(category=director, name_ru="Директор представительства",
                                       name_en='Representative Office Director',
                                       name_tr='Temsilcilik Direktörü', name_de='Niederlassungsleiter', name_zh='代表处总监')

        ItemSubcategory.objects.create(category=director, name_ru="Директор по строительству",
                                       name_en='Construction Director',
                                       name_tr='İnşaat Direktörü', name_de='Baudirektor', name_zh='建筑总监')

        ItemSubcategory.objects.create(category=director, name_ru="Директор по производству",
                                       name_en='Production Director',
                                       name_tr='Üretim Direktörü', name_de='Produktionsleiter', name_zh='生产总监')

        # merchandiser~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        merchandiser = ItemCategory.objects.create(name_ru="Мерчандайзер", name_en='Merchandiser',
                                                   name_tr='Merchandiser',
                                                   name_de='Merchandiser', name_zh='陈列员',
                                                   purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=merchandiser, name_ru="Визуальный мерчандайзер",
                                       name_en='Visual Merchandiser',
                                       name_tr='Görsel Merchandiser', name_de='Visueller Merchandiser', name_zh='视觉陈列员')

        ItemSubcategory.objects.create(category=merchandiser, name_ru="Мерчандайзер", name_en='Merchandiser',
                                       name_tr='Merchandiser', name_de='Merchandiser', name_zh='陈列员')

        ItemSubcategory.objects.create(category=merchandiser, name_ru="Старший мерчандайзер",
                                       name_en='Senior Merchandiser',
                                       name_tr='Kıdemli Merchandiser', name_de='Senior Merchandiser', name_zh='高级陈列员')

        # engineer~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        engineer = ItemCategory.objects.create(name_ru="Инженер", name_en='Engineer', name_tr='Mühendis',
                                               name_de='Ingenieur', name_zh='工程师', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер", name_en='Engineer',
                                       name_tr='Mühendis', name_de='Ingenieur', name_zh='工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер-конструктор", name_en='Design Engineer',
                                       name_tr='Tasarım Mühendisi', name_de='Konstruktionsingenieur', name_zh='设计工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Главный инженер", name_en='Chief Engineer',
                                       name_tr='Baş Mühendis', name_de='Chefingenieur', name_zh='首席工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер-механик", name_en='Mechanical Engineer',
                                       name_tr='Mekanik Mühendis', name_de='Maschinenbauingenieur', name_zh='机械工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер ПТО", name_en='Production Engineer',
                                       name_tr='Üretim Mühendisi', name_de='Produktionsingenieur', name_zh='生产工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер-строитель", name_en='Civil Engineer',
                                       name_tr='İnşaat Mühendisi', name_de='Bauingenieur', name_zh='土木工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер-сметчик", name_en='Estimation Engineer',
                                       name_tr='Maliyet Mühendisi', name_de='Kostenschätzer', name_zh='估算工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер-электрик", name_en='Electrical Engineer',
                                       name_tr='Elektrik Mühendisi', name_de='Elektroingenieur', name_zh='电气工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер по охране труда", name_en='Safety Engineer',
                                       name_tr='İş Güvenliği Mühendisi', name_de='Sicherheitsingenieur',
                                       name_zh='安全工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер-программист", name_en='Software Engineer',
                                       name_tr='Yazılım Mühendisi', name_de='Softwareingenieur', name_zh='软件工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер-эколог", name_en='Environmental Engineer',
                                       name_tr='Çevre Mühendisi', name_de='Umweltingenieur', name_zh='环境工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Сервисный инженер", name_en='Service Engineer',
                                       name_tr='Servis Mühendisi', name_de='Serviceingenieur', name_zh='服务工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер технической поддержки",
                                       name_en='Technical Support Engineer',
                                       name_tr='Teknik Destek Mühendisi', name_de='Technischer Support Ingenieur',
                                       name_zh='技术支持工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер-энергетик", name_en='Energy Engineer',
                                       name_tr='Enerji Mühendisi', name_de='Energieingenieur', name_zh='能源工程师')

        ItemSubcategory.objects.create(category=engineer, name_ru="Инженер связи", name_en='Communication Engineer',
                                       name_tr='İletişim Mühendisi', name_de='Kommunikationsingenieur', name_zh='通信工程师')

        # accountant~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        accountant = ItemCategory.objects.create(name_ru="Бухгалтер", name_en='Accountant', name_tr='Muhasebeci',
                                                 name_de='Buchhalter', name_zh='会计', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=accountant, name_ru="Заместитель главного бухгалтера",
                                       name_en='Deputy Chief Accountant',
                                       name_tr='Baş Muhasebe Müdür Yardımcısı',
                                       name_de='Stellvertretender Leiter der Buchhaltung', name_zh='副总会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Бухгалтер-экономист",
                                       name_en='Economist Accountant',
                                       name_tr='Ekonomist Muhasebeci', name_de='Wirtschaftsbuchhalter',
                                       name_zh='经济学家会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Бухгалтер-кассир", name_en='Accountant Cashier',
                                       name_tr='Kasiyer Muhasebeci', name_de='Kassierer Buchhalter', name_zh='出纳会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Бухгалтер по расчету заработной платы",
                                       name_en='Payroll Accountant',
                                       name_tr='Maaş Muhasebecisi', name_de='Lohnbuchhalter', name_zh='工资会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Экономист-бухгалтер",
                                       name_en='Economist Accountant',
                                       name_tr='Ekonomist Muhasebeci', name_de='Wirtschaftsbuchhalter',
                                       name_zh='经济学家会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Старший бухгалтер", name_en='Senior Accountant',
                                       name_tr='Kıdemli Muhasebeci', name_de='Senior Buchhalter', name_zh='高级会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Ведущий бухгалтер", name_en='Lead Accountant',
                                       name_tr='Baş Muhasebeci', name_de='Leitender Buchhalter', name_zh='主会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Бухгалтер на первичную документацию",
                                       name_en='Accountant for Primary Documentation',
                                       name_tr='İlköğretim Dokümantasyon Muhasebecisi',
                                       name_de='Buchhalter für Primärdokumentation', name_zh='初级文件会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Бухгалтер-калькулятор",
                                       name_en='Accountant Calculator',
                                       name_tr='Muhasebeci Hesap Makinesi', name_de='Buchhalterrechner',
                                       name_zh='会计计算器')

        ItemSubcategory.objects.create(category=accountant, name_ru="Помошник бухгалтера",
                                       name_en='Assistant Accountant',
                                       name_tr='Muhasebe Asistanı', name_de='Assistent Buchhalter', name_zh='助理会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Бухгалтер по учету тмц",
                                       name_en='Accountant for TMC Accounting',
                                       name_tr='TMC Muhasebe Muhasebecisi', name_de='Buchhalter für TMC-Buchhaltung',
                                       name_zh='TMC会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Бухгалтер по банковским операциям",
                                       name_en='Bank Operations Accountant',
                                       name_tr='Banka Operasyonları Muhasebecisi', name_de='Bankbetriebsbuchhalter',
                                       name_zh='银行业务会计师')

        ItemSubcategory.objects.create(category=accountant, name_ru="Помощник главного бухгалтера",
                                       name_en='Assistant Chief Accountant',
                                       name_tr='Baş Muhasebe Yardımcısı', name_de='Assistent des Leitenden Buchhalters',
                                       name_zh='首席会计师助手')

        ItemSubcategory.objects.create(category=accountant, name_ru="Ассистент бухгалтера",
                                       name_en='Accountant Assistant',
                                       name_tr='Muhasebe Asistanı', name_de='Buchhalterassistent', name_zh='会计助手')

        # specialist~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        specialist = ItemCategory.objects.create(name_ru="Специалист", name_en='Specialist', name_tr='Uzman',
                                                 name_de='Spezialist', name_zh='专家', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по работе с клиентами",
                                       name_en='Customer Service Specialist',
                                       name_tr='Müşteri Hizmetleri Uzmanı', name_de='Kundendienstspezialist',
                                       name_zh='客户服务专员')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по логистике",
                                       name_en='Logistics Specialist',
                                       name_tr='Lojistik Uzmanı', name_de='Logistikspezialist', name_zh='物流专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Кредитный специалист", name_en='Credit Specialist',
                                       name_tr='Kredi Uzmanı', name_de='Kreditspezialist', name_zh='信贷专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по продажам",
                                       name_en='Sales Specialist',
                                       name_tr='Satış Uzmanı', name_de='Verkaufsspezialist', name_zh='销售专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по кадрам", name_en='HR Specialist',
                                       name_tr='İK Uzmanı', name_de='HR-Spezialist', name_zh='人力资源专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист отдела кадров",
                                       name_en='HR Department Specialist',
                                       name_tr='İK Departmanı Uzmanı', name_de='HR-Abteilungsspezialist',
                                       name_zh='人力资源部专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Технический специалист",
                                       name_en='Technical Specialist',
                                       name_tr='Teknik Uzman', name_de='Technikspezialist', name_zh='技术专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по закупкам",
                                       name_en='Procurement Specialist',
                                       name_tr='Satın Alma Uzmanı', name_de='Beschaffungsspezialist', name_zh='采购专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист технической поддержки",
                                       name_en='Technical Support Specialist',
                                       name_tr='Teknik Destek Uzmanı', name_de='Technischer Support Spezialist',
                                       name_zh='技术支持专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по связям с общественностью",
                                       name_en='Public Relations Specialist',
                                       name_tr='Halkla İlişkiler Uzmanı',
                                       name_de='Spezialist für Öffentlichkeitsarbeit', name_zh='公关专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по таможенному оформлению",
                                       name_en='Customs Clearance Specialist',
                                       name_tr='Gümrük İşlemleri Uzmanı', name_de='Zollsachbearbeiter', name_zh='清关专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист кредитного отдела",
                                       name_en='Credit Department Specialist',
                                       name_tr='Kredi Departmanı Uzmanı', name_de='Spezialist für Kreditabteilung',
                                       name_zh='信贷部门专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по подбору персонала",
                                       name_en='Recruitment Specialist',
                                       name_tr='İK Seçme Uzmanı', name_de='Spezialist für Personalbeschaffung',
                                       name_zh='招聘专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по кредитованию",
                                       name_en='Lending Specialist',
                                       name_tr='Kredi Uzmanı', name_de='Kreditspezialist', name_zh='放款专家')

        ItemSubcategory.objects.create(category=specialist, name_ru="Специалист по страхованию",
                                       name_en='Insurance Specialist',
                                       name_tr='Sigorta Uzmanı', name_de='Versicherungsspezialist', name_zh='保险专家')

        # operator~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        operator = ItemCategory.objects.create(name_ru="Оператор", name_en='Operator', name_tr='Operatör',
                                               name_de='Operator', name_zh='操作员', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор ПК", name_en='PC Operator',
                                       name_tr='PC Operatörü', name_de='PC Operator', name_zh='PC 操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор call-центра",
                                       name_en='Call Center Operator',
                                       name_tr='Çağrı Merkezi Operatörü', name_de='Callcenter Operator',
                                       name_zh='呼叫中心操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор", name_en='Operator',
                                       name_tr='Operatör', name_de='Operator', name_zh='操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор на телефоне", name_en='Phone Operator',
                                       name_tr='Telefon Operatörü', name_de='Telefon Operator', name_zh='电话操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор базы данных", name_en='Database Operator',
                                       name_tr='Veritabanı Operatörü', name_de='Datenbank Operator', name_zh='数据库操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор АЗС", name_en='Gas Station Operator',
                                       name_tr='Akaryakıt İstasyonu Operatörü', name_de='Tankstellenoperator',
                                       name_zh='加油站操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор 1C", name_en='1C Operator',
                                       name_tr='1C Operatörü', name_de='1C Operator', name_zh='1C 操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор БД", name_en='Database Operator',
                                       name_tr='Veritabanı Operatörü', name_de='Datenbank Operator', name_zh='数据库操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор производственной линии",
                                       name_en='Production Line Operator',
                                       name_tr='Üretim Hattı Operatörü', name_de='Produktionslinienoperator',
                                       name_zh='生产线操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Кладовщик-оператор", name_en='Warehouse Operator',
                                       name_tr='Depo Operatörü', name_de='Lageroperator', name_zh='仓库操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор линии", name_en='Line Operator',
                                       name_tr='Hat Operatörü', name_de='Linienoperator', name_zh='线路操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор-кассир", name_en='Cashier Operator',
                                       name_tr='Kasiyer Operatör', name_de='Kassenoperator', name_zh='收银员操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор склада", name_en='Warehouse Operator',
                                       name_tr='Depo Operatörü', name_de='Lageroperator', name_zh='仓库操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор по добыче нефти и газа",
                                       name_en='Oil and Gas Extraction Operator',
                                       name_tr='Petrol ve Gaz Çıkarım Operatörü',
                                       name_de='Öl- und Gasförderungsoperator', name_zh='石油和天然气开采操作员')

        ItemSubcategory.objects.create(category=operator, name_ru="Оператор ЭВМ", name_en='Computer Operator',
                                       name_tr='Bilgisayar Operatörü', name_de='Computer Operator', name_zh='计算机操作员')

        # assistant~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        assistant = ItemCategory.objects.create(name_ru="Помощник", name_en='Assistant', name_tr='Asistan',
                                                name_de='Assistent', name_zh='助手', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник руководителя",
                                       name_en='Executive Assistant',
                                       name_tr='Yönetici Asistanı', name_de='Führungskräfteassistent', name_zh='高级助理')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник системного администратора",
                                       name_en='System Administrator Assistant',
                                       name_tr='Sistem Yöneticisi Asistanı', name_de='Systemadministratorassistent',
                                       name_zh='系统管理员助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Личный помощник руководителя",
                                       name_en='Personal Assistant',
                                       name_tr='Kişisel Asistan', name_de='Persönlicher Assistent', name_zh='私人助理')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник экономиста", name_en='Economist Assistant',
                                       name_tr='Ekonomist Asistanı', name_de='Wirtschaftsassistent', name_zh='经济学家助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник менеджера по персоналу",
                                       name_en='HR Manager Assistant',
                                       name_tr='İK Yöneticisi Asistanı', name_de='HR-Managerassistent',
                                       name_zh='人力资源经理助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник дизайнера", name_en='Designer Assistant',
                                       name_tr='Tasarımcı Asistanı', name_de='Designerassistent', name_zh='设计师助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник маркетолога",
                                       name_en='Marketing Assistant',
                                       name_tr='Pazarlama Asistanı', name_de='Marketingassistent', name_zh='市场营销助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник аудитора", name_en='Auditor Assistant',
                                       name_tr='Denetçi Asistanı', name_de='Rechnungsprüfungsassistent',
                                       name_zh='审计师助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник генерального директора",
                                       name_en='CEO Assistant',
                                       name_tr='CEO Asistanı', name_de='CEO-Assistent', name_zh='首席执行官助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник менеджера по продажам",
                                       name_en='Sales Manager Assistant',
                                       name_tr='Satış Yöneticisi Asistanı', name_de='Vertriebsleiterassistent',
                                       name_zh='销售经理助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник адвоката", name_en='Lawyer Assistant',
                                       name_tr='Avukat Asistanı', name_de='Anwaltsassistent', name_zh='律师助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник логиста", name_en='Logistics Assistant',
                                       name_tr='Lojistik Asistan', name_de='Logistikassistent', name_zh='物流助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник финансового менеджера",
                                       name_en='Finance Manager Assistant',
                                       name_tr='Maliye Yöneticisi Asistanı', name_de='Finanzmanagerassistent',
                                       name_zh='财务经理助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник бурильщика", name_en='Driller Assistant',
                                       name_tr='Delici Asistanı', name_de='Bohrerassistent', name_zh='钻孔工助手')

        ItemSubcategory.objects.create(category=assistant, name_ru="Помощник менеджера по туризму",
                                       name_en='Tourism Manager Assistant',
                                       name_tr='Turizm Yöneticisi Asistanı', name_de='Tourismusmanagerassistent',
                                       name_zh='旅游经理助手')

        # courier~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        courier = ItemCategory.objects.create(name_ru="Курьер", name_en='Courier', name_tr='Kurye',
                                              name_de='Kurier', name_zh='快递员', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=courier, name_ru="Водитель-курьер", name_en='Driver Courier',
                                       name_tr='Sürücü Kurye', name_de='Fahrer Kurier', name_zh='驾驶员快递员')

        ItemSubcategory.objects.create(category=courier, name_ru="Курьер-экспедитор", name_en='Courier Expeditor',
                                       name_tr='Kurye Ekspeditör', name_de='Kurier-Expeditor', name_zh='快递员调度员')

        ItemSubcategory.objects.create(category=courier, name_ru="Курьер-водитель", name_en='Courier Driver',
                                       name_tr='Kurye Sürücü', name_de='Kurierfahrer', name_zh='快递员驾驶员')

        ItemSubcategory.objects.create(category=courier, name_ru="Курьер с автомобилем", name_en='Courier with Car',
                                       name_tr='Arabası Olan Kurye', name_de='Kurier mit Auto', name_zh='有车的快递员')

        ItemSubcategory.objects.create(category=courier, name_ru="Экспедитор-курьер", name_en='Expeditor Courier',
                                       name_tr='Ekspeditör Kurye', name_de='Expeditor Kurier', name_zh='调度员快递员')

        # loader~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        loader = ItemCategory.objects.create(name_ru="Грузчик", name_en='Loader', name_tr='Yükleyici',
                                             name_de='Lader', name_zh='装载员', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=loader, name_ru="Грузчик-комплектовщик", name_en='Loader-Picker',
                                       name_tr='Yükleyici-Picker', name_de='Lader-Picker', name_zh='装载员-拣货员')

        ItemSubcategory.objects.create(category=loader, name_ru="Грузчик-экспедитор", name_en='Loader-Expeditor',
                                       name_tr='Yükleyici-Ekspeditör', name_de='Lader-Expeditor', name_zh='装载员-调度员')

        ItemSubcategory.objects.create(category=loader, name_ru="Кладовщик-грузчик", name_en='Warehouse Loader',
                                       name_tr='Depo Yükleyici', name_de='Lager Lader', name_zh='仓库装载员')

        ItemSubcategory.objects.create(category=loader, name_ru="Экспедитор-грузчик", name_en='Expeditor Loader',
                                       name_tr='Ekspeditör Yükleyici', name_de='Expeditor Lader', name_zh='调度员装载员')

        ItemSubcategory.objects.create(category=loader, name_ru="Комплектовщик-грузчик", name_en='Picker-Loader',
                                       name_tr='Picker Yükleyici', name_de='Picker Lader', name_zh='拣货员装载员')

        ItemSubcategory.objects.create(category=loader, name_ru="Грузчик-кладовщик", name_en='Loader-Warehouseman',
                                       name_tr='Yükleyici-Depocu', name_de='Lader-Lagerarbeiter', name_zh='装载员-仓库工人')

        ItemSubcategory.objects.create(category=loader, name_ru="Бригадир смены грузчиков-комплектовщиков",
                                       name_en='Shift Supervisor of Loaders-Pickers',
                                       name_tr='Yükleyici-Picker Vardiya Sorumlusu',
                                       name_de='Schichtleiter der Lader-Picker', name_zh='装载员-拣货员班组长')

        ItemSubcategory.objects.create(category=loader, name_ru="Водитель погрузчика-грузчик",
                                       name_en='Forklift Driver-Loader',
                                       name_tr='Forklift Sürücüsü-Yükleyici', name_de='Gabelstaplerfahrer-Lader',
                                       name_zh='叉车司机-装载员')

        ItemSubcategory.objects.create(category=loader, name_ru="Грузчик-наборщик", name_en='Loader-Packer',
                                       name_tr='Yükleyici-Packer', name_de='Lader-Packer', name_zh='装载员-打包员')

        ItemSubcategory.objects.create(category=loader, name_ru="Рабочий-грузчик", name_en='Worker-Loader',
                                       name_tr='İşçi-Yükleyici', name_de='Arbeiter-Lader', name_zh='工人-装载员')

        # manager~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        manager = ItemCategory.objects.create(name_ru="Менеджер", name_en='Manager', name_tr='Yönetici',
                                              name_de='Manager', name_zh='经理', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер по работе с клиентами",
                                       name_en='Customer Relationship Manager',
                                       name_tr='Müşteri İlişkileri Yöneticisi', name_de='Kundenbeziehungsmanager',
                                       name_zh='客户关系经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Офис-менеджер", name_en='Office Manager',
                                       name_tr='Ofis Yöneticisi', name_de='Büroleiter', name_zh='办公室经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер по персоналу", name_en='HR Manager',
                                       name_tr='İK Yöneticisi', name_de='HR-Manager', name_zh='人力资源经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер по закупкам", name_en='Procurement Manager',
                                       name_tr='Satın Alma Yöneticisi', name_de='Beschaffungsmanager', name_zh='采购经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер по туризму", name_en='Tourism Manager',
                                       name_tr='Turizm Yöneticisi', name_de='Tourismusmanager', name_zh='旅游经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Финансовый менеджер", name_en='Finance Manager',
                                       name_tr='Finans Yöneticisi', name_de='Finanzmanager', name_zh='财务经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Региональный менеджер", name_en='Regional Manager',
                                       name_tr='Bölgesel Yönetici', name_de='Regionalmanager', name_zh='区域经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер проекта", name_en='Project Manager',
                                       name_tr='Proje Yöneticisi', name_de='Projektmanager', name_zh='项目经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер по логистике", name_en='Logistics Manager',
                                       name_tr='Lojistik Yöneticisi', name_de='Logistikmanager', name_zh='物流经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер проектов", name_en='Project Manager',
                                       name_tr='Proje Yöneticisi', name_de='Projektmanager', name_zh='项目经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер по развитию бизнеса",
                                       name_en='Business Development Manager',
                                       name_tr='İş Geliştirme Yöneticisi', name_de='Business Development Manager',
                                       name_zh='业务拓展经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер по продажам автомобилей",
                                       name_en='Car Sales Manager',
                                       name_tr='Otomobil Satış Yöneticisi', name_de='Autoverkaufsleiter',
                                       name_zh='汽车销售经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Территориальный менеджер",
                                       name_en='Territory Manager',
                                       name_tr='Bölgesel Yönetici', name_de='Gebietsleiter', name_zh='地区经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Менеджер по ВЭД", name_en='Foreign Trade Manager',
                                       name_tr='Dış Ticaret Yöneticisi', name_de='Außenhandelsmanager',
                                       name_zh='国际贸易经理')

        ItemSubcategory.objects.create(category=manager, name_ru="Контент-менеджер", name_en='Content Manager',
                                       name_tr='İçerik Yöneticisi', name_de='Content Manager', name_zh='内容经理')

        # storekeeper~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        storekeeper = ItemCategory.objects.create(name_ru="Кладовщик", name_en='Storekeeper', name_tr='Depo Görevlisi',
                                                  name_de='Lagerverwalter', name_zh='仓库管理员',
                                                  purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик", name_en='Storekeeper',
                                       name_tr='Depo Görevlisi', name_de='Lagerverwalter', name_zh='仓库管理员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик-оператор",
                                       name_en='Storekeeper Operator',
                                       name_tr='Depo Operatörü', name_de='Lageroperator', name_zh='仓库操作员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик-комплектовщик",
                                       name_en='Storekeeper-Picker',
                                       name_tr='Depo Görevlisi-Picker', name_de='Lagerverwalter-Picker',
                                       name_zh='仓库管理员-拣货员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Старший кладовщик", name_en='Senior Storekeeper',
                                       name_tr='Kıdemli Depo Görevlisi', name_de='Senior Lagerverwalter',
                                       name_zh='高级仓库管理员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик-грузчик", name_en='Storekeeper-Loader',
                                       name_tr='Depo Görevlisi-Yükleyici', name_de='Lagerverwalter-Lader',
                                       name_zh='仓库管理员-装载员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик-отборщик", name_en='Storekeeper-Picker',
                                       name_tr='Depo Görevlisi-Picker', name_de='Lagerverwalter-Picker',
                                       name_zh='仓库管理员-拣货员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Помощник кладовщика",
                                       name_en='Storekeeper Assistant',
                                       name_tr='Depo Görevlisi Yardımcısı', name_de='Lagerverwalter-Assistent',
                                       name_zh='仓库管理员助理')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик-наборщик", name_en='Storekeeper-Packer',
                                       name_tr='Depo Görevlisi-Paketleyici', name_de='Lagerverwalter-Packer',
                                       name_zh='仓库管理员-打包员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик-экспедитор",
                                       name_en='Storekeeper-Expeditor',
                                       name_tr='Depo Görevlisi-Ekspeditör', name_de='Lagerverwalter-Expeditor',
                                       name_zh='仓库管理员-调度员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Грузчик-кладовщик", name_en='Loader-Storekeeper',
                                       name_tr='Yükleyici-Depo Görevlisi', name_de='Lader-Lagerverwalter',
                                       name_zh='装载员-仓库管理员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик группы отгрузки",
                                       name_en='Storekeeper of Shipment Group', name_tr='Sevkiyat Grubu Depo Görevlisi',
                                       name_de='Lagerverwalter der Versandgruppe', name_zh='发货组仓库管理员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик группы приемки",
                                       name_en='Storekeeper of Reception Group',
                                       name_tr='Teslimat Grubu Depo Görevlisi',
                                       name_de='Lagerverwalter der Empfangsgruppe', name_zh='接收组仓库管理员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик материального склада",
                                       name_en='Material Warehouse Storekeeper', name_tr='Malzeme Depo Görevlisi',
                                       name_de='Lagerverwalter des Materiallagers', name_zh='物料仓库管理员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик по возвратам",
                                       name_en='Storekeeper for Returns', name_tr='İade Depo Görevlisi',
                                       name_de='Lagerverwalter für Rücksendungen', name_zh='退货仓库管理员')

        ItemSubcategory.objects.create(category=storekeeper, name_ru="Кладовщик по работе с возвратами",
                                       name_en='Storekeeper for Handling Returns', name_tr='İade İşleme Depo Görevlisi',
                                       name_de='Lagerverwalter für die Bearbeitung von Rücksendungen',
                                       name_zh='处理退货的仓库管理员')

        # worker~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        worker = ItemCategory.objects.create(name_ru="Рабочий", name_en='Worker', name_tr='İşçi',
                                             name_de='Arbeiter', name_zh='工人', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=worker, name_ru="Дорожный рабочий", name_en='Road Worker',
                                       name_tr='Yol İşçisi', name_de='Straßenarbeiter', name_zh='道路工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Кухонный рабочий", name_en='Kitchen Worker',
                                       name_tr='Mutfak İşçisi', name_de='Küchenarbeiter', name_zh='厨房工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Подсобный рабочий", name_en='Auxiliary Worker',
                                       name_tr='Yardımcı İşçi', name_de='Hilfsarbeiter', name_zh='辅助工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Рабочий по комплексному обслуживанию зданий",
                                       name_en='Building Complex Maintenance Worker',
                                       name_tr='Bina Kompleks Bakım İşçisi', name_de='Gebäudekomplexwartung',
                                       name_zh='建筑综合维护工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Рабочий по комплексному обслуживанию производства",
                                       name_en='Production Complex Maintenance Worker',
                                       name_tr='Üretim Kompleks Bakım İşçisi', name_de='Produktionskomplexwartung',
                                       name_zh='生产综合维护工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Рабочий по комплектации сувенирной продукции",
                                       name_en='Souvenir Production Assembly Worker',
                                       name_tr='Hatıra Üretim Montaj İşçisi',
                                       name_de='Souvenir Produktionsmontagearbeiter',
                                       name_zh='纪念品生产装配工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Рабочий по обслуживанию зданий и сооружений",
                                       name_en='Building and Structure Maintenance Worker',
                                       name_tr='Bina ve Yapı Bakım İşçisi', name_de='Gebäude- und Strukturerhaltung',
                                       name_zh='建筑和结构维护工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Рабочий по ремонту зданий",
                                       name_en='Building Repair Worker',
                                       name_tr='Bina Tamir İşçisi', name_de='Gebäudereparaturarbeiter',
                                       name_zh='建筑修理工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Рабочий погрузочно-разгрузочных работ",
                                       name_en='Loading and Unloading Worker',
                                       name_tr='Yükleme ve Boşaltma İşçisi', name_de='Verlade- und Entladearbeiter',
                                       name_zh='装卸工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Рабочий склада",
                                       name_en='Warehouse Worker',
                                       name_tr='Depo İşçisi', name_de='Lagerarbeiter',
                                       name_zh='仓库工人')

        ItemSubcategory.objects.create(category=worker, name_ru="Рабочий-грузчик",
                                       name_en='Worker-Loader',
                                       name_tr='İşçi-Yükleyici', name_de='Arbeiter-Lader',
                                       name_zh='工人-装载员')

        ItemSubcategory.objects.create(category=worker, name_ru="Специалист-рабочий",
                                       name_en='Specialist Worker',
                                       name_tr='Uzman İşçi', name_de='Spezialistenarbeiter',
                                       name_zh='专业工人')

        # driver~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        driver = ItemCategory.objects.create(name_ru="Водитель", name_en='Driver', name_tr='Şoför',
                                             name_de='Fahrer', name_zh='司机', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель-экспедитор", name_en='Driver-Expeditor',
                                       name_tr='Şoför-Kurye', name_de='Fahrer-Expeditor', name_zh='司机-快递员')

        ItemSubcategory.objects.create(category=driver, name_ru="Личный водитель", name_en='Personal Driver',
                                       name_tr='Kişisel Şoför', name_de='Persönlicher Fahrer', name_zh='私人司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель погрузчика", name_en='Forklift Driver',
                                       name_tr='Forklift Operatörü', name_de='Gabelstaplerfahrer', name_zh='叉车司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель-курьер", name_en='Driver-Courier',
                                       name_tr='Şoför-Kurye', name_de='Fahrer-Kurier', name_zh='司机-快递员')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель персональный", name_en='Personal Driver',
                                       name_tr='Kişisel Şoför', name_de='Persönlicher Fahrer', name_zh='私人司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель-охранник", name_en='Driver-Security Guard',
                                       name_tr='Şoför-Güvenlik Görevlisi', name_de='Fahrer-Sicherheitsbeauftragter',
                                       name_zh='司机-安保人员')

        ItemSubcategory.objects.create(category=driver, name_ru="Персональный водитель руководителя",
                                       name_en='Personal Driver for Executive',
                                       name_tr='Yönetici İçin Kişisel Şoför',
                                       name_de='Persönlicher Fahrer für Führungskräfte',
                                       name_zh='高管的私人司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель электропогрузчика",
                                       name_en='Electric Forklift Driver',
                                       name_tr='Elektrikli Forklift Operatörü',
                                       name_de='Elektrischer Gabelstaplerfahrer',
                                       name_zh='电动叉车司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель-международник",
                                       name_en='International Driver',
                                       name_tr='Uluslararası Şoför', name_de='Internationaler Fahrer', name_zh='国际司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель-дальнобойщик",
                                       name_en='Long-Haul Driver',
                                       name_tr='Uzun Mesafe Şoförü', name_de='Langstreckenfahrer', name_zh='长途司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель-механик",
                                       name_en='Driver-Mechanic',
                                       name_tr='Şoför-Mekanik', name_de='Fahrer-Mechaniker', name_zh='司机-机械师')

        ItemSubcategory.objects.create(category=driver, name_ru="Водитель-инкассатор",
                                       name_en='Driver-Cash Collector',
                                       name_tr='Şoför-Tahsilatçı', name_de='Fahrer-Geldeinzahler', name_zh='司机-现金收款员')

        ItemSubcategory.objects.create(category=driver, name_ru="Курьер-водитель",
                                       name_en='Courier-Driver',
                                       name_tr='Kurye-Şoför', name_de='Kurier-Fahrer', name_zh='快递员-司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Механик-водитель",
                                       name_en='Mechanic-Driver',
                                       name_tr='Mekanik-Şoför', name_de='Mechaniker-Fahrer', name_zh='机械师-司机')

        ItemSubcategory.objects.create(category=driver, name_ru="Охранник-водитель",
                                       name_en='Security Guard-Driver',
                                       name_tr='Güvenlik Görevlisi-Şoför', name_de='Sicherheitsbeauftragter-Fahrer',
                                       name_zh='安保人员-司机')

        # administrator~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        administrator = ItemCategory.objects.create(name_ru="Администратор", name_en='Administrator',
                                                    name_tr='Yönetici', name_de='Administrator', name_zh='管理员',
                                                    purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=administrator, name_ru="Системный администратор",
                                       name_en='System Administrator',
                                       name_tr='Sistem Yöneticisi', name_de='Systemadministrator', name_zh='系统管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор салона красоты",
                                       name_en='Beauty Salon Administrator',
                                       name_tr='Güzellik Salonu Yöneticisi',
                                       name_de='Administrator des Schönheitssalons',
                                       name_zh='美容院管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор магазина",
                                       name_en='Store Administrator',
                                       name_tr='Mağaza Yöneticisi', name_de='Geschäftsadministrator', name_zh='商店管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор офиса",
                                       name_en='Office Administrator',
                                       name_tr='Ofis Yöneticisi', name_de='Büroadministrator', name_zh='办公室管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Помощник системного администратора",
                                       name_en='Assistant System Administrator',
                                       name_tr='Asistan Sistem Yöneticisi', name_de='Assistent Systemadministrator',
                                       name_zh='助理系统管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор ресторана",
                                       name_en='Restaurant Administrator',
                                       name_tr='Restoran Yöneticisi', name_de='Restaurantadministrator',
                                       name_zh='餐厅管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Менеджер-администратор",
                                       name_en='Manager Administrator',
                                       name_tr='Yönetici Yöneticisi', name_de='Manageradministrator', name_zh='经理管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор торгового зала",
                                       name_en='Sales Floor Administrator',
                                       name_tr='Satış Alanı Yöneticisi', name_de='Verkaufsraumadministrator',
                                       name_zh='销售区管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор баз данных",
                                       name_en='Database Administrator',
                                       name_tr='Veritabanı Yöneticisi', name_de='Datenbankadministrator',
                                       name_zh='数据库管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор гостиницы",
                                       name_en='Hotel Administrator',
                                       name_tr='Otel Yöneticisi', name_de='Hoteladministrator', name_zh='酒店管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор сайта",
                                       name_en='Website Administrator',
                                       name_tr='Web Sitesi Yöneticisi', name_de='Websiteadministrator', name_zh='网站管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор проекта",
                                       name_en='Project Administrator',
                                       name_tr='Proje Yöneticisi', name_de='Projektadministrator', name_zh='项目管理员')

        ItemSubcategory.objects.create(category=administrator, name_ru="Администратор-менеджер",
                                       name_en='Administrator Manager',
                                       name_tr='Yönetici Yönetici', name_de='Administrator-Manager', name_zh='管理员经理')

        ItemSubcategory.objects.create(category=administrator, name_ru="Системный администратор Windows",
                                       name_en='Windows System Administrator',
                                       name_tr='Windows Sistem Yöneticisi', name_de='Windows Systemadministrator',
                                       name_zh='Windows系统管理员')

        # seller~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        seller = ItemCategory.objects.create(name_ru="Продавец", name_en='Seller',
                                             name_tr='Satıcı', name_de='Verkäufer', name_zh='销售员',
                                             purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец-консультант",
                                       name_en='Sales Consultant',
                                       name_tr='Satış Danışmanı', name_de='Verkaufsberater', name_zh='销售顾问')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец",
                                       name_en='Seller',
                                       name_tr='Satıcı', name_de='Verkäufer', name_zh='销售员')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец-кассир",
                                       name_en='Seller Cashier',
                                       name_tr='Kasiyer Satıcı', name_de='Verkäufer-Kassierer', name_zh='销售收银员')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец-консультант автомобилей",
                                       name_en='Car Sales Consultant',
                                       name_tr='Otomobil Satış Danışmanı', name_de='Autoverkaufsberater',
                                       name_zh='汽车销售顾问')

        ItemSubcategory.objects.create(category=seller, name_ru="Старший продавец",
                                       name_en='Senior Seller',
                                       name_tr='Kıdemli Satıcı', name_de='Senior Verkäufer', name_zh='高级销售员')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец непродовольственных товаров",
                                       name_en='Non-food Seller',
                                       name_tr='Gıda Dışı Satıcı', name_de='Non-food Verkäufer',
                                       name_zh='非食品销售员')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец-консультант мебели",
                                       name_en='Furniture Sales Consultant',
                                       name_tr='Mobilya Satış Danışmanı', name_de='Möbelverkaufsberater',
                                       name_zh='家具销售顾问')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец-консультант выходного дня",
                                       name_en='Weekend Sales Consultant',
                                       name_tr='Hafta Sonu Satış Danışmanı', name_de='Wochenendverkaufsberater',
                                       name_zh='周末销售顾问')

        ItemSubcategory.objects.create(category=seller, name_ru="Кассир-продавец",
                                       name_en='Cashier Seller',
                                       name_tr='Kasiyer Satıcı', name_de='Kassierer Verkäufer', name_zh='收银员销售员')

        ItemSubcategory.objects.create(category=seller, name_ru="Старший продавец-кассир",
                                       name_en='Senior Seller Cashier',
                                       name_tr='Kıdemli Satıcı Kasiyer', name_de='Senior Verkäufer-Kassierer',
                                       name_zh='高级销售员收银员')

        ItemSubcategory.objects.create(category=seller, name_ru="Старший продавец-консультант",
                                       name_en='Senior Sales Consultant',
                                       name_tr='Kıdemli Satış Danışmanı', name_de='Senior Verkaufsberater',
                                       name_zh='高级销售顾问')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец автозапчастей",
                                       name_en='Auto Parts Seller',
                                       name_tr='Oto Parça Satıcısı', name_de='Autoersatzteil Verkäufer',
                                       name_zh='汽车零部件销售员')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец-консультант одежды",
                                       name_en='Clothing Sales Consultant',
                                       name_tr='Giyim Satış Danışmanı', name_de='Bekleidungsverkaufsberater',
                                       name_zh='服装销售顾问')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец компьютерной техники",
                                       name_en='Computer Equipment Seller',
                                       name_tr='Bilgisayar Ekipmanı Satıcısı', name_de='Computer Equipment Verkäufer',
                                       name_zh='计算机设备销售员')

        ItemSubcategory.objects.create(category=seller, name_ru="Продавец автомобилей",
                                       name_en='Car Seller',
                                       name_tr='Oto Satıcısı', name_de='Autoverkäufer', name_zh='汽车销售员')

        # security~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        security = ItemCategory.objects.create(name_ru="Охранник", name_en='Security Guard',
                                               name_tr='Güvenlik Görevlisi', name_de='Sicherheitsbeauftragter',
                                               name_zh='安保人员', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=security, name_ru="Охранник",
                                       name_en='Security Guard',
                                       name_tr='Güvenlik Görevlisi', name_de='Sicherheitsbeauftragter',
                                       name_zh='安保人员')

        ItemSubcategory.objects.create(category=security, name_ru="Водитель-охранник",
                                       name_en='Driver Security Guard',
                                       name_tr='Sürücü Güvenlik Görevlisi', name_de='Fahrer Sicherheitsbeauftragter',
                                       name_zh='司机安保人员')

        ItemSubcategory.objects.create(category=security, name_ru="Личный охранник",
                                       name_en='Personal Bodyguard',
                                       name_tr='Kişisel Güvenlik Görevlisi',
                                       name_de='Persönlicher Sicherheitsbeauftragter',
                                       name_zh='私人保镖')

        ItemSubcategory.objects.create(category=security, name_ru="Администратор-охранник",
                                       name_en='Administrator Security Guard',
                                       name_tr='Yönetici Güvenlik Görevlisi',
                                       name_de='Administrator Sicherheitsbeauftragter',
                                       name_zh='管理员安保人员')

        ItemSubcategory.objects.create(category=security, name_ru="Охранник-водитель",
                                       name_en='Guard Driver',
                                       name_tr='Güvenlik Görevlisi Sürücü', name_de='Sicherheitsbeauftragter Fahrer',
                                       name_zh='安保人员司机')

        ItemSubcategory.objects.create(category=security, name_ru="Персональный водитель-охранник",
                                       name_en='Personal Driver Security Guard',
                                       name_tr='Kişisel Sürücü Güvenlik Görevlisi',
                                       name_de='Persönlicher Fahrer Sicherheitsbeauftragter',
                                       name_zh='私人司机安保人员')

        ItemSubcategory.objects.create(category=security, name_ru="Контролер-охранник",
                                       name_en='Controller Security Guard',
                                       name_tr='Kontrolör Güvenlik Görevlisi',
                                       name_de='Controller Sicherheitsbeauftragter',
                                       name_zh='控制器安保人员')

        ItemSubcategory.objects.create(category=security, name_ru="Сторож-охранник",
                                       name_en='Watchman Security Guard',
                                       name_tr='Nöbetçi Güvenlik Görevlisi', name_de='Wachmann Sicherheitsbeauftragter',
                                       name_zh='看门人安保人员')

        ItemSubcategory.objects.create(category=security, name_ru="Старший охранник",
                                       name_en='Senior Security Guard',
                                       name_tr='Kıdemli Güvenlik Görevlisi', name_de='Senior Sicherheitsbeauftragter',
                                       name_zh='高级安保人员')

        # cleaner~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        cleaner = ItemCategory.objects.create(name_ru="Уборщик", name_en='Cleaner',
                                              name_tr='Temizlik Görevlisi', name_de='Reiniger',
                                              name_zh='清洁工', purchase_type=ItemCategory.RESUME)

        ItemSubcategory.objects.create(category=cleaner, name_ru="Уборщик",
                                       name_en='Cleaner',
                                       name_tr='Temizlik Görevlisi', name_de='Reiniger',
                                       name_zh='清洁工')

        ItemSubcategory.objects.create(category=cleaner, name_ru="Уборщик административных помещений",
                                       name_en='Office Cleaner',
                                       name_tr='Ofis Temizlik Görevlisi', name_de='Büroreiniger',
                                       name_zh='办公室清洁工')

        ItemSubcategory.objects.create(category=cleaner, name_ru="Уборщик офисных помещений",
                                       name_en='Office Cleaner',
                                       name_tr='Ofis Temizlik Görevlisi', name_de='Büroreiniger',
                                       name_zh='办公室清洁工')

        ItemSubcategory.objects.create(category=cleaner, name_ru="Уборщик помещений",
                                       name_en='Room Cleaner',
                                       name_tr='Oda Temizlik Görevlisi', name_de='Raumreiniger',
                                       name_zh='房间清洁工')

        ItemSubcategory.objects.create(category=cleaner, name_ru="Уборщик производственных и служебных помещений",
                                       name_en='Industrial and Service Area Cleaner',
                                       name_tr='Endüstriyel ve Hizmet Alanı Temizlik Görevlisi',
                                       name_de='Industrie- und Servicebereichsreiniger',
                                       name_zh='工业和服务区清洁工')

        ItemSubcategory.objects.create(category=cleaner, name_ru="Уборщик производственных помещений",
                                       name_en='Industrial Cleaner',
                                       name_tr='Endüstriyel Temizlik Görevlisi', name_de='Industriereiniger',
                                       name_zh='工业清洁工')

        ItemSubcategory.objects.create(category=cleaner, name_ru="Уборщик служебных помещений",
                                       name_en='Service Area Cleaner',
                                       name_tr='Hizmet Alanı Temizlik Görevlisi', name_de='Servicebereichsreiniger',
                                       name_zh='服务区清洁工')

        return Response(data={'message': _('ItemCategories added successfully')}, status=status.HTTP_200_OK)

