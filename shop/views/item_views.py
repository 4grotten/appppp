import calendar
from django.utils.translation import activate
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
    OrganizationResumeRequestAcceptedSerializer
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
        ResumeRequestService.process_user_resume_request(sender_user=sender_user, organization=organization,
                                                         item=item, show_contacts=show_contacts,
                                                         phone_numbers=phone_numbers, links=links)

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
        ResumeRequestService.process_organization_resume_request(user=request.user,
                                                                 sender_organization=sender_organization,
                                                                 organization=organization, item=item,
                                                                 show_contacts=show_contacts,
                                                                 phone_numbers=phone_numbers,
                                                                 links=links)

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


class TranslateNamesOfItemSubategoryV1(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        name_translations = {
            'Квартира': {'de': 'Wohnung', 'zh': '公寓'},
            'Вилла': {'de': 'Villa', 'zh': '别墅'},
            'Таунхаус': {'de': 'Reihenhaus', 'zh': '联排别墅'},
            'Пентхаус': {'de': 'Penthouse', 'zh': '顶层公寓'},
            'Соединение': {'de': 'Verbindung', 'zh': '连接'},
            'Дуплекс': {'de': 'Duplex', 'zh': '复式'},
            'Полный Этаж': {'de': 'Ganze Etage', 'zh': '整层'},
            'Целое Здание': {'de': 'Gebäude', 'zh': '整栋建筑'},
            'Земля': {'de': 'Land', 'zh': '土地'},
            'Единица Оптовой Продажи': {'de': 'Einheit im Großhandel', 'zh': '批发单位'},
            'Отель и Гостиничные апартаменты': {'de': 'Hotel und Hotelapartments', 'zh': '酒店和酒店公寓'},
            'Квартира Аренда': {'de': 'Wohnung mieten', 'zh': '公寓租赁'},
            'Вилла Аренда': {'de': 'Villa mieten', 'zh': '别墅租赁'},
            'Таунхаус Аренда': {'de': 'Reihenhaus mieten', 'zh': '联排别墅租赁'},
            'Пентхаус Аренда': {'de': 'Penthouse mieten', 'zh': '顶层公寓租赁'},
            'Соединение Аренда': {'de': 'Verbindung mieten', 'zh': '连接租赁'},
            'Дуплекс Аренда': {'de': 'Duplex mieten', 'zh': '复式租赁'},
            'Полный Этаж Аренда': {'de': 'Ganze Etage mieten', 'zh': '整层租赁'},
            'Целое Здание Аренда': {'de': 'Gebäude mieten', 'zh': '整栋建筑租赁'},
            'Единица Оптовой Аренды': {'de': 'Einheit im Großhandel mieten', 'zh': '批发单位租赁'},
            'Бунгало Аренда': {'de': 'Bungalow mieten', 'zh': '平房租赁'},
            'Отель и Апартаменты в отелях Аренда': {'de': 'Hotel und Hotelapartments mieten', 'zh': '酒店和酒店公寓租赁'},
            'Все для мамы': {'de': 'Alles für Mama', 'zh': '为妈妈准备的一切'},
            'Белье': {'de': 'Unterwäsche', 'zh': '内衣'},
            'Брюки': {'de': 'Hosen', 'zh': '裤子'},
            'Верхняя одежда': {'de': 'Oberbekleidung', 'zh': '外套'},
            'Водолазки': {'de': 'Rollkragenpullover', 'zh': '高领毛衣'},
            'Джемперы': {'de': 'Pullover', 'zh': '毛衣'},
            'Джинсы': {'de': 'Jeans', 'zh': '牛仔裤'},
            'Жакеты': {'de': 'Jacken', 'zh': '夹克'},
            'Жилеты': {'de': 'Westen', 'zh': '马甲'},
            'Кардиганы': {'de': 'Strickjacken', 'zh': '开衫'},
            'Карнавальные костюмы': {'de': 'Karnevalskostüme', 'zh': '化妆舞会服装'},
            'Кигуруми': {'de': 'Kigurumi', 'zh': '卡哇伊睡衣'},
            'Колготки': {'de': 'Strumpfhosen', 'zh': '连裤袜'},
            'Комбинезоны': {'de': 'Overall', 'zh': '连体衣'},
            'Костюмы': {'de': 'Kostüme', 'zh': '服装'},
            'Плавки': {'de': 'Badehosen', 'zh': '泳裤'},
            'Лонгсливы': {'de': 'Langarmshirts', 'zh': '长袖衬衫'},
            'Мантии': {'de': 'Mäntel', 'zh': '斗篷'},
            'Медицинская одежда': {'de': 'Medizinische Kleidung', 'zh': '医疗服'},
            'Носки': {'de': 'Socken', 'zh': '袜子'},
            'Обувь для жениха': {'de': 'Schuhe für den Bräutigam', 'zh': '新郎鞋'},
            'Одежда для дома': {'de': 'Hauskleidung', 'zh': '家居服'},
            'Одежда для отдыха': {'de': 'Freizeitkleidung', 'zh': '休闲服'},
            'Одноразовые изделия': {'de': 'Einwegprodukte', 'zh': '一次性用品'},
            'Пиджаки': {'de': 'Sakkos', 'zh': '西装外套'},
            'Смокинги': {'de': 'Smokings', 'zh': '燕尾服'},
            'Пляжная одежда': {'de': 'Strandkleidung', 'zh': '沙滩服'},
            'Пуловеры': {'de': 'Strickpullover', 'zh': '套头毛衣'},
            'Рабочая обувь': {'de': 'Arbeitsschuhe', 'zh': '工作鞋'},
            'Религиозная одежда': {'de': 'Religiöse Kleidung', 'zh': '宗教服装'},
            'Рубашки': {'de': 'Hemden', 'zh': '衬衫'},
            'Свитера': {'de': 'Strickwaren', 'zh': '毛衣'},
            'Средства защиты органов дыхания': {'de': 'Atemschutzmittel', 'zh': '呼吸器防护'},
            'Средства индивидуальной защиты': {'de': 'Persönliche Schutzausrüstung', 'zh': '个人防护用品'},
            'Термобелье': {'de': 'Thermounterwäsche', 'zh': '保暖内衣'},
            'Топы': {'de': 'Oberteile', 'zh': '上衣'},
            'Униформа и рабочая одежда': {'de': 'Uniform und Arbeitskleidung', 'zh': '制服和工作服'},
            'Футболки': {'de': 'T-Shirts', 'zh': 'T恤'},
            'Блузки': {'de': 'Blusen', 'zh': '衬衫'},
            'Купальники': {'de': 'Badeanzüge', 'zh': '比基尼'},
            'Обувь для невесты': {'de': 'Brautschuhe', 'zh': '新娘鞋'},
            'Обувь для подружек невесты': {'de': 'Schuhe für Brautjungfern', 'zh': '伴娘鞋'},
            'Одежда для кормящих мам': {'de': 'Kleidung für stillende Mütter', 'zh': '哺乳妈妈服装'},
            'Платья подружек невесты': {'de': 'Kleider für Brautjungfern', 'zh': '伴娘服'},
            'Сарафаны': {'de': 'Trägerkleider', 'zh': '吊带裙'},
            'Свадебные платья': {'de': 'Brautkleider', 'zh': '婚纱'},
            'Собираемся в роддом': {'de': 'Vorbereitung auf die Entbindung', 'zh': '准备去产房'},
            'Туники': {'de': 'Tuniken', 'zh': '束腰长袍'},
            'Чулки': {'de': 'Strümpfe', 'zh': '长筒袜'},
            'Бордшорты': {'de': 'Boardshorts', 'zh': '潮流短裤'},
            'Аксессуары для кормления': {'de': 'Stillzubehör', 'zh': '哺乳配件'},
            'Аксессуары для купания': {'de': 'Badezubehör', 'zh': '洗澡配件'},
            'Безопасность ребенка': {'de': 'Kindersicherheit', 'zh': '儿童安全'},
            'Боди и ползунки': {'de': 'Strampler und Bodysuits', 'zh': '连体衣和爬行裤'},
            'Болеро': {'de': 'Bolero', 'zh': '短外套'},
            'Влажные салфетки': {'de': 'Feuchttücher', 'zh': '湿巾'},
            'Гигиена и уход': {'de': 'Hygiene und Pflege', 'zh': '卫生与护理'},
            'Конверты и спальные мешки': {'de': 'Umschläge und Schlafsäcke', 'zh': '被套和睡袋'},
            'Кофточки': {'de': 'Jäckchen', 'zh': '短外套'},
            'Одежда на выписку': {'de': 'Kleidung für die Entlassung', 'zh': '出院服'},
            'Пеленки, слюнявчики, царапки': {'de': 'Windeln, Lätzchen, Kratzschutz', 'zh': '尿布、围嘴、防刮护套'},
            'Передвижение': {'de': 'Bewegung', 'zh': '移动'},
            'Платья': {'de': 'Kleider', 'zh': '连衣裙'},
            'Постельные принадлежности': {'de': 'Bettwäsche', 'zh': '床上用品'},
            'Распашонки': {'de': 'Strampelanzüge', 'zh': '连体衣'},
            'Свитшоты': {'de': 'Sweatshirts', 'zh': '卫衣'},
            'Толстовки': {'de': 'Sweatshirts', 'zh': '卫衣'},
            'Фартуки': {'de': 'Schürzen', 'zh': '围裙'},
            'Футболки и майки': {'de': 'T-Shirts und Tanktops', 'zh': 'T恤和背心'},
            'Футболки и топы': {'de': 'T-Shirts und Tops', 'zh': 'T恤和上衣'},
            'Худи': {'de': 'Kapuzenpullover', 'zh': '连帽衫'},
            'Шорты': {'de': 'Kurze Hosen', 'zh': '短裤'},
            'Штаны': {'de': 'Hosen', 'zh': '裤子'},
            'Юбки': {'de': 'Röcke', 'zh': '裙子'},
            'Дошкольные рюкзаки': {'de': 'Kindergartenrucksäcke', 'zh': '学前背包'},
            'Ленты выпускника': {'de': 'Abschlussbänder', 'zh': '毕业纪念带'},
            'Обувь для девочек': {'de': 'Mädchenschuhe', 'zh': '女童鞋'},
            'Обувь для мальчиков': {'de': 'Jungenschuhe', 'zh': '男童鞋'},
            'Одежда для девочек': {'de': 'Mädchenkleidung', 'zh': '女童服装'},
            'Одежда для мальчиков': {'de': 'Jungenkleidung', 'zh': '男童服装'},
            'Ранцы': {'de': 'Rucksäcke', 'zh': '背包'},
            'Спорт': {'de': 'Sport', 'zh': '运动'},
            'Школьные принадлежности': {'de': 'Schulbedarf', 'zh': '学校用品'},
            'Школьные рюкзаки': {'de': 'Schulrucksäcke', 'zh': '学校背包'},
            'Автокресла': {'de': 'Autokindersitze', 'zh': '汽车儿童座椅'},
            'Багаж': {'de': 'Gepäck', 'zh': '行李'},
            'Бытовая техника для детей': {'de': 'Haushaltsgeräte für Kinder', 'zh': '儿童家用电器'},
            'Детские коляски': {'de': 'Kinderwagen', 'zh': '婴儿车'},
            'Детские конструкторы': {'de': 'Kinderbaukästen', 'zh': '儿童积木'},
            'Детский транспорт': {'de': 'Kinderfahrzeuge', 'zh': '儿童交通工具'},
            'Защитные средства и гигиена для детей': {'de': 'Schutzmittel und Hygieneartikel für Kinder',
                                                      'zh': '儿童防护用品和卫生用品'},
            'Зимние товары': {'de': 'Winterartikel', 'zh': '冬季用品'},
            'Игровое оружие': {'de': 'Spielzeugwaffen', 'zh': '玩具武器'},
            'Игровые наборы и фигурки': {'de': 'Spielsets und Figuren', 'zh': '游戏套装和玩偶'},
            'Игрушки для малышей и дошкольников': {'de': 'Spielzeug für Babys und Vorschulkinder', 'zh': '婴儿和学龄前儿童玩具'},
            'Игрушки на радиоуправлении': {'de': 'Ferngesteuertes Spielzeug', 'zh': '遥控玩具'},
            'Крупногабаритные качели': {'de': 'Großformatige Schaukeln', 'zh': '大尺寸秋千'},
            'Летние товары': {'de': 'Sommerartikel', 'zh': '夏季用品'},
            'Музыкальные инструменты': {'de': 'Musikinstrumente', 'zh': '乐器'},
            'Надувные игрушки': {'de': 'Aufblasbare Spielzeuge', 'zh': '充气玩具'},
            'Переноски для детей': {'de': 'Kindertragen', 'zh': '儿童背带'},
            'Питание': {'de': 'Ernährung', 'zh': '食品'},
            'Плавание и развлечения на воде': {'de': 'Schwimmen und Wasserspaß', 'zh': '游泳和水上娱乐'},
            'Принадлежности для салона автомобиля': {'de': 'Autozubehör', 'zh': '汽车内饰配件'},
            'Слинги и рюкзаки': {'de': 'Tragetücher und Rucksäcke', 'zh': '背带和背包'},
            'Сюжетно ролевые игры': {'de': 'Rollenspiele', 'zh': '角色扮演游戏'},
            'Электроника для детей': {'de': 'Elektronik für Kinder', 'zh': '儿童电子产品'},
            'Балетки и чешки': {'de': 'Ballerinas und Clogs', 'zh': '芭蕾舞鞋和木底鞋'},
            'Босоножки и сандалии': {'de': 'Sandalen und Sandalen', 'zh': '凉鞋和凉鞋'},
            'Сабо и мюли': {'de': 'Sabo und Mules', 'zh': '凉鞋和木底凉鞋'},
            'Балетки': {'de': 'Ballerinas', 'zh': '芭蕾舞鞋'},
            'Биркенштоки': {'de': 'Birkenstocks', 'zh': '比肯斯托克'},
            'Босоножки': {'de': 'Sandalen', 'zh': '凉鞋'},
            'Ботинки': {'de': 'Stiefel', 'zh': '靴子'},
            'Ботфорты': {'de': 'Stiefel', 'zh': '靴子'},
            'Валенки': {'de': 'Filzstiefel', 'zh': '毡靴'},
            'Галоши': {'de': 'Gamaschen', 'zh': '套鞋'},
            'Дутики': {'de': 'Dutiks', 'zh': '杜蒂克斯'},
            'Кеды': {'de': 'Turnschuhe', 'zh': '运动鞋'},
            'Кроссовки': {'de': 'Sportschuhe', 'zh': '运动鞋'},
            'Лоферы': {'de': 'Loafer', 'zh': '乐福鞋'},
            'Луноходы': {'de': 'Mondwanderer', 'zh': '月球车'},
            'Мокасины': {'de': 'Mokassins', 'zh': '便鞋'},
            'Пантолеты': {'de': 'Hausschuhe', 'zh': '拖鞋'},
            'Пинетки': {'de': 'Strickschuhe', 'zh': '针织鞋'},
            'Полуботинки': {'de': 'Halbschuhe', 'zh': '半鞋'},
            'Полусапожки': {'de': 'Halbstiefel', 'zh': '半靴'},
            'Резиновые сапоги': {'de': 'Gummistiefel', 'zh': '橡胶靴'},
            'Сабо': {'de': 'Sabo', 'zh': '凉鞋'},
            'Сандалии': {'de': 'Sandalen', 'zh': '凉鞋'},
            'Сапоги': {'de': 'Stiefel', 'zh': '靴子'},
            'Слиперы': {'de': 'Hausschuhe', 'zh': '拖鞋'},
            'Слипоны': {'de': 'Slip-Ons', 'zh': '便鞋'},
            'Сникеры': {'de': 'Sneakers', 'zh': '运动鞋'},
            'Сноубутсы': {'de': 'Schneestiefel', 'zh': '雪地靴'},
            'Топсайдеры': {'de': 'Top-Sider', 'zh': '上层便鞋'},
            'Туфли': {'de': 'Schuhe', 'zh': '鞋子'},
            'Угги': {'de': 'Uggs', 'zh': '雪地靴'},
            'Унты': {'de': 'Unges', 'zh': '靴子'},
            'Шлепанцы': {'de': 'Flip-Flops', 'zh': '人字拖鞋'},
            'Эспадрильи': {'de': 'Espadrilles', 'zh': '草编鞋'},
            'Ботинки и полуботинки': {'de': 'Stiefel und Halbschuhe', 'zh': '靴子和半鞋'},
            'Кеды и кроссовки': {'de': 'Turnschuhe und Sportschuhe', 'zh': '运动鞋和运动鞋'},
            'Мокасины и топсайдеры': {'de': 'Mokassins und Top-Sider', 'zh': '便鞋和上层便鞋'},
            'Сапоги и унты': {'de': 'Stiefel und Stiefel', 'zh': '靴子和靴子'},
            'Тапочки': {'de': 'Hausschuhe', 'zh': '拖鞋'},
            'Туфли и лоферы': {'de': 'Schuhe und Loafer', 'zh': '鞋子和乐福鞋'},
            'Шлепанцы и аквасоки': {'de': 'Flip-Flops und Aquasocks', 'zh': '人字拖鞋和水鞋'},
            'Для девочек': {'de': 'Für Mädchen', 'zh': '给女孩'},
            'Для мальчиков': {'de': 'Für Jungen', 'zh': '给男孩'},
            'Для новорожденных': {'de': 'Für Neugeborene', 'zh': '给新生儿'},
            'Аксессуары для обуви': {'de': 'Schuhzubehör', 'zh': '鞋配件'},
            'Вкусные подарки': {'de': 'Leckere Geschenke', 'zh': '美味礼品'},
            'Чай и кофе': {'de': 'Tee und Kaffee', 'zh': '茶和咖啡'},
            'Сладости и хлебобулочные изделия': {'de': 'Süßigkeiten und Backwaren', 'zh': '糖果和面点'},
            'Бакалея': {'de': 'Lebensmittel', 'zh': '杂货'},
            'Детское питание': {'de': 'Kinderernährung', 'zh': '儿童食品'},
            'Добавки пищевые': {'de': 'Lebensmittelzusatzstoffe', 'zh': '食品添加剂'},
            'Здоровое питание': {'de': 'Gesunde Ernährung', 'zh': '健康饮食'},
            'Мясная продукция': {'de': 'Fleischprodukte', 'zh': '肉类制品'},
            'Молоко и сливки': {'de': 'Milch und Sahne', 'zh': '牛奶和奶油'},
            'Напитки': {'de': 'Getränke', 'zh': '饮料'},
            'Снеки': {'de': 'Snacks', 'zh': '小吃'},
            'Для кошек': {'de': 'Für Katzen', 'zh': '猫用品'},
            'Для собак': {'de': 'Für Hunde', 'zh': '狗用品'},
            'Для птиц': {'de': 'Für Vögel', 'zh': '鸟类用品'},
            'Для грызунов и хорьков': {'de': 'Für Nagetiere und Frettchen', 'zh': '啮齿动物和雪貂用品'},
            'Для лошадей': {'de': 'Für Pferde', 'zh': '马用品'},
            'Аквариумистика': {'de': 'Aquaristik', 'zh': '水族'},
            'Террариумистика': {'de': 'Terraristik', 'zh': '爬行动物用品'},
            'Бумажная продукция': {'de': 'Papierprodukte', 'zh': '纸制品'},
            'Карты и глобусы': {'de': 'Karten und Globen', 'zh': '地图和地球仪'},
            'Офисные принадлежности': {'de': 'Bürobedarf', 'zh': '办公用品'},
            'Пеналы': {'de': 'Stifthalter', 'zh': '文具盒'},
            'Письменные принадлежности': {'de': 'Schreibwaren', 'zh': '写字工具'},
            'Счетный материал': {'de': 'Zählmaterial', 'zh': '计数材料'},
            'Торговые принадлежности': {'de': 'Handelszubehör', 'zh': '贸易用品'},
            'Чертежные принадлежности': {'de': 'Zeichenzubehör', 'zh': '制图工具'},
            'Витамины и БАДы': {'de': 'Vitamine und Nahrungsergänzungsmittel', 'zh': '维生素和补充剂'},
            'Дезинфекция, стерилизация и утилизация': {'de': 'Desinfektion, Sterilisation und Entsorgung',
                                                       'zh': '消毒，灭菌和处理'},
            'Контрацептивы и лубриканты': {'de': 'Verhütungsmittel und Gleitmittel', 'zh': '避孕药和润滑剂'},
            'Лекарственные препараты': {'de': 'Medikamente', 'zh': '药品'},
            'Лечебное питание': {'de': 'Heilnahrung', 'zh': '治疗性食品'},
            'Маски защитные': {'de': 'Schutzmasken', 'zh': '防护口罩'},
            'Медицинские изделия': {'de': 'Medizinische Produkte', 'zh': '医疗用品'},
            'Медицинские приборы': {'de': 'Medizinische Geräte', 'zh': '医疗器械'},
            'Оздоровление': {'de': 'Gesundheit', 'zh': '健康'},
            'Оптика': {'de': 'Optik', 'zh': '光学'},
            'Ортопедия': {'de': 'Orthopädie', 'zh': '矫形'},
            'Реабилитация': {'de': 'Rehabilitation', 'zh': '康复'},
            'Уход за полостью рта': {'de': 'Mundhygiene', 'zh': '口腔护理'},
            'Электроинструменты': {'de': 'Elektrowerkzeuge', 'zh': '电动工具'},
            'Строительное оборудование': {'de': 'Bauausrüstung', 'zh': '建筑设备'},
            'Инструменты и оснастка': {'de': 'Werkzeuge und Zubehör', 'zh': '工具和配件'},
            'Сантехника': {'de': 'Sanitärtechnik', 'zh': '卫生设备'},
            'Отделочные материалы': {'de': 'Veredelungsmaterialien', 'zh': '装修材料'},
            'Хранение инструментов': {'de': 'Werkzeugaufbewahrung', 'zh': '工具存储'},
            'Электрика': {'de': 'Elektrik', 'zh': '电气设备'},
            'Ванная': {'de': 'Badezimmer', 'zh': '浴室'},
            'Кухня': {'de': 'Küche', 'zh': '厨房'},
            'Предметы интерьера': {'de': 'Inneneinrichtung', 'zh': '室内装饰品'},
            'Спальня': {'de': 'Schlafzimmer', 'zh': '卧室'},
            'Гостиная': {'de': 'Wohnzimmer', 'zh': '客厅'},
            'Дача': {'de': 'Datscha', 'zh': '别墅'},
            'Детская': {'de': 'Kinderzimmer', 'zh': '儿童房'},
            'Досуг и творчество': {'de': 'Freizeit und Kreativität', 'zh': '娱乐和创意'},
            'Зеркала': {'de': 'Spiegel', 'zh': '镜子'},
            'Кронштейны': {'de': 'Halterungen', 'zh': '支架'},
            'Освещение': {'de': 'Beleuchtung', 'zh': '照明'},
            'Зажигалки': {'de': 'Feuerzeuge', 'zh': '打火机'},
            'Отдых на природе': {'de': 'Outdoor-Freizeit', 'zh': '户外休闲'},
            'Мебель': {'de': 'Möbel', 'zh': '家具'},
            'Прихожая': {'de': 'Diele', 'zh': '门厅'},
            'Хозяйственные товары': {'de': 'Haushaltswaren', 'zh': '家居用品'},
            'Хранение вещей': {'de': 'Aufbewahrung von Dingen', 'zh': '物品存储'},
            'Шторы': {'de': 'Vorhänge', 'zh': '窗帘'},
            'Аварийные принадлежности': {'de': 'Notfallausrüstung', 'zh': '紧急用品'},
            'Автоаксессуары': {'de': 'Autozubehör', 'zh': '汽车配件'},
            'Автозапчасти': {'de': 'Autoersatzteile', 'zh': '汽车零件'},
            'Автомобильная электроника': {'de': 'Autoelektronik', 'zh': '汽车电子设备'},
            'Внешний декор': {'de': 'Außendekoration', 'zh': '户外装饰'},
            'Инструменты и оборудование': {'de': 'Werkzeuge und Ausrüstung', 'zh': '工具和设备'},
            'Мототовары': {'de': 'Motorradartikel', 'zh': '摩托车用品'},
            'Обустройство салона': {'de': 'Inneneinrichtung des Autos', 'zh': '车内装饰'},
            'Уход за автомобилем': {'de': 'Autopflege', 'zh': '汽车护理'},
            'Шины и Диски': {'de': 'Reifen und Felgen', 'zh': '轮胎和轮毂'},
            'Кольца': {'de': 'Ringe', 'zh': '戒指'},
            'Серьги': {'de': 'Ohrringe', 'zh': '耳环'},
            'Браслеты': {'de': 'Armbänder', 'zh': '手链'},
            'Подвески и шармы': {'de': 'Anhänger und Charms', 'zh': '吊坠和魅力'},
            'Комплекты': {'de': 'Sets', 'zh': '套装'},
            'Колье, цепи, шнурки': {'de': 'Halsketten, Ketten, Schnüre', 'zh': '项链，链条，绳子'},
            'Броши': {'de': 'Broschen', 'zh': '胸针'},
            'Пирсинг': {'de': 'Piercing', 'zh': '穿孔'},
            'Часы': {'de': 'Uhren', 'zh': '手表'},
            'Зажимы, запонки, ремни': {'de': 'Clips, Manschettenknöpfe, Gürtel', 'zh': '夹子，袖扣，腰带'},
            'Четки': {'de': 'Gebetskette', 'zh': '念珠'},
            'Сувениры и столовое серебро': {'de': 'Souvenirs und Silbergeschirr', 'zh': '纪念品和银器'},
            'Украшения из золота': {'de': 'Goldschmuck', 'zh': '金饰'},
            'Украшения из серебра': {'de': 'Silberschmuck', 'zh': '银饰'},
            'Украшения из керамики': {'de': 'Keramikschmuck', 'zh': '陶瓷饰品'},
            'Аксессуары для украшений': {'de': 'Schmuckzubehör', 'zh': '饰品配件'},
            'Белье и аксессуары': {'de': 'Wäsche und Accessoires', 'zh': '内衣和配饰'},
            'Игры и сувениры': {'de': 'Spiele und Souvenirs', 'zh': '游戏和纪念品'},
            'Интимная косметика': {'de': 'Intimkosmetik', 'zh': '私密护肤品'},
            'Интимная съедобная косметика': {'de': 'Essbare Intimkosmetik', 'zh': '可食用私密护肤品'},
            'Презервативы и лубриканты': {'de': 'Kondome und Gleitmittel', 'zh': '避孕套和润滑剂'},
            'Секс игрушки': {'de': 'Sexspielzeug', 'zh': '性玩具'},
            'Фетиш и БДСМ': {'de': 'Fetisch und BDSM', 'zh': '恋物癖和BDSM'},
            'Аксессуары для волос': {'de': 'Haarzubehör', 'zh': '发饰'},
            'Аксессуары для одежды': {'de': 'Kleidungszubehör', 'zh': '服饰配饰'},
            'Бижутерия': {'de': 'Schmuck', 'zh': '珠宝首饰'},
            'Веера': {'de': 'Fächer', 'zh': '折扇'},
            'Галстуки и бабочки': {'de': 'Krawatten und Fliegen', 'zh': '领带和蝴蝶结'},
            'Головные уборы': {'de': 'Kopfbedeckungen', 'zh': '头饰'},
            'Зеркальца': {'de': 'Spiegel', 'zh': '小镜子'},
            'Зонты': {'de': 'Regenschirme', 'zh': '雨伞'},
            'Кошельки и кредитницы': {'de': 'Geldbörsen und Kreditkartenetuis', 'zh': '钱包和信用卡夹'},
            'Маски для сна': {'de': 'Schlafmasken', 'zh': '睡眠面罩'},
            'Носовые платки': {'de': 'Taschentücher', 'zh': '手帕'},
            'Очки и футляры': {'de': 'Brillen und Etuis', 'zh': '眼镜和眼镜盒'},
            'Перчатки и варежки': {'de': 'Handschuhe und Fäustlinge', 'zh': '手套和拳套'},
            'Платки и шарфы': {'de': 'Tücher und Schals', 'zh': '围巾和披肩'},
            'Религиозные': {'de': 'Religiöse', 'zh': '宗教的'},
            'Ремни и пояса': {'de': 'Gürtel', 'zh': '腰带'},
            'Сумки и рюкзаки': {'de': 'Taschen und Rucksäcke', 'zh': '包和背包'},
            'Часы и ремешки': {'de': 'Uhren und Armbänder', 'zh': '手表和手链'},
            'Чемоданы и защита багажа': {'de': 'Koffer und Gepäckschutz', 'zh': '行李箱和行李保护'},
            'Автоэлектроника и навигация': {'de': 'Autoelektronik und Navigation', 'zh': '汽车电子和导航'},
            'Гарнитуры и наушники': {'de': 'Headsets und Kopfhörer', 'zh': '耳机和头戴式耳机'},
            'Детская электроника': {'de': 'Kindelektronik', 'zh': '儿童电子产品'},
            'Игровые консоли и игры': {'de': 'Spielekonsolen und Spiele', 'zh': '游戏机和游戏'},
            'Кабели и зарядные устройства': {'de': 'Kabel und Ladegeräte', 'zh': '电缆和充电器'},
            'Музыка и видео': {'de': 'Musik und Video', 'zh': '音乐和视频'},
            'Цифровые видеокурсы': {'de': 'Digitale Videokurse', 'zh': '数字视频课程'},
            'Ноутбуки и компьютеры': {'de': 'Laptops und Computer', 'zh': '笔记本电脑和电脑'},
            'Офисная техника': {'de': 'Bürotechnik', 'zh': '办公设备'},
            'Развлечения и гаджеты': {'de': 'Unterhaltung und Gadgets', 'zh': '娱乐和小工具'},
            'Сетевое оборудование': {'de': 'Netzwerkgeräte', 'zh': '网络设备'},
            'Системы безопасности': {'de': 'Sicherheitssysteme', 'zh': '安全系统'},
            'Смартфоны и телефоны': {'de': 'Smartphones und Telefone', 'zh': '智能手机和电话'},
            'Смарт-часы и браслеты': {'de': 'Smartwatches und Armbänder', 'zh': '智能手表和手环'},
            'ТВ, Аудио, Фото, Видео техника': {'de': 'TV, Audio, Foto, Video Technik', 'zh': '电视，音频，照片，视频技术'},
            'Торговое оборудование': {'de': 'Handelsausrüstung', 'zh': '商业设备'},
            'Умный дом': {'de': 'Smart Home', 'zh': '智能家居'},
            'Элементы питания': {'de': 'Batterien', 'zh': '电池'},
            'Электротранспорт и аксессуары': {'de': 'Elektrofahrzeuge und Zubehör', 'zh': '电动交通工具和配件'},
            'Климатическая техника': {'de': 'Klimatechnik', 'zh': '气候技术'},
            'Красота и здоровье': {'de': 'Schönheit und Gesundheit', 'zh': '美容和健康'},
            'Садовая техника': {'de': 'Gartentechnik', 'zh': '园艺技术'},
            'Техника для дома': {'de': 'Haustechnik', 'zh': '家用电器'},
            'Техника для кухни': {'de': 'Küchentechnik', 'zh': '厨房电器'},
            'Крупная бытовая техника': {'de': 'Großgeräte', 'zh': '大型家电'},
            'Детям и родителям': {'de': 'Für Kinder und Eltern', 'zh': '给儿童和父母'},
            'Учебная литература': {'de': 'Lehrmaterial', 'zh': '教科书'},
            'Энциклопедии': {'de': 'Enzyklopädien', 'zh': '百科全书'},
            'Нехудожественная литература': {'de': 'Sachliteratur', 'zh': '非小说类文学'},
            'Художественная литература': {'de': 'Belletristik', 'zh': '小说'},
            'Цифровые книги': {'de': 'Digitale Bücher', 'zh': '数字图书'},
            'Журналы': {'de': 'Zeitschriften', 'zh': '杂志'},
            'Книги родословные': {'de': 'Genealogiebücher', 'zh': '家谱书'},
            'Коллекционные издания': {'de': 'Sammlerausgaben', 'zh': '收藏版'},
            'Букинистика': {'de': 'Antiquariat', 'zh': '古董书籍'},
            'Блокноты творческие': {'de': 'Kreative Notizbücher', 'zh': '创意笔记本'},
            'Мультимедиа': {'de': 'Multimedia', 'zh': '多媒体'},
            'Аудиокниги': {'de': 'Hörbücher', 'zh': '有声书'},
            'Альпинизм': {'de': 'Bergsteigen', 'zh': '登山'},
            'Бадминтон': {'de': 'Badminton', 'zh': '羽毛球'},
            'Бег': {'de': 'Laufen', 'zh': '跑步'},
            'Бильярд': {'de': 'Billard', 'zh': '台球'},
            'Велосипеды': {'de': 'Fahrräder', 'zh': '自行车'},
            'Велоспорт': {'de': 'Radsport', 'zh': '自行车运动'},
            'Видеотренировки': {'de': 'Video-Training', 'zh': '视频训练'},
            'Водные виды спорта': {'de': 'Wassersport', 'zh': '水上运动'},
            'Гимнастика': {'de': 'Gymnastik', 'zh': '体操'},
            'Гольф': {'de': 'Golf', 'zh': '高尔夫'},
            'Дартс': {'de': 'Darts', 'zh': '飞镖'},
            'Единоборства': {'de': 'Kampfsport', 'zh': '武术'},
            'Защита': {'de': 'Selbstverteidigung', 'zh': '防护'},
            'Зимние виды спорта': {'de': 'Wintersport', 'zh': '冬季运动'},
            'Зимний Инвентарь': {'de': 'Winterausrüstung', 'zh': '冬季装备'},
            'Зимняя Рыбалка': {'de': 'Winterangeln', 'zh': '冬季钓鱼'},
            'Йога': {'de': 'Yoga', 'zh': '瑜伽'},
            'Кемпинговая мебель': {'de': 'Campingmöbel', 'zh': '露营家具'},
            'Командные виды спорта': {'de': 'Mannschaftssport', 'zh': '团队运动'},
            'Конный спорт': {'de': 'Pferdesport', 'zh': '马术运动'},
            'Летний Инвентарь': {'de': 'Sommerausrüstung', 'zh': '夏季装备'},
            'Мотоспорт': {'de': 'Motorsport', 'zh': '摩托运动'},
            'Обувь': {'de': 'Schuhe', 'zh': '鞋类'},
            'Одежда': {'de': 'Kleidung', 'zh': '服装'},
            'Охота': {'de': 'Jagd', 'zh': '狩猎'},
            'Охота и рыбалка': {'de': 'Jagd und Angeln', 'zh': '狩猎和钓鱼'},
            'Палатки, шатры, тенты': {'de': 'Zelte, Pavillons, Zelte', 'zh': '帐篷，遮篷，帐篷'},
            'Парусный спорт': {'de': 'Segelsport', 'zh': '帆船运动'},
            'Пейнтбол': {'de': 'Paintball', 'zh': '彩弹'},
            'Пилатес': {'de': 'Pilates', 'zh': '普拉提'},
            'Подводная охота': {'de': 'Unterwasserjagd', 'zh': '水下狩猎'},
            'Поддержка и восстановление': {'de': 'Unterstützung und Erholung', 'zh': '支持和恢复'},
            'Походная кухня': {'de': 'Campingküche', 'zh': '露营厨房'},
            'Походы': {'de': 'Wanderungen', 'zh': '徒步旅行'},
            'Ролики': {'de': 'Rollschuhe', 'zh': '滑轮鞋'},
            'Роликовые коньки': {'de': 'Inlineskaten', 'zh': '轮滑'},
            'Рыбалка': {'de': 'Angeln', 'zh': '钓鱼'},
            'Рюкзаки, сумки и баулы': {'de': 'Rucksäcke, Taschen und Koffer', 'zh': '背包，包和箱子'},
            'Самокаты': {'de': 'Roller', 'zh': '滑板车'},
            'Скалолазание': {'de': 'Klettern', 'zh': '攀岩'},
            'Скейтборды': {'de': 'Skateboards', 'zh': '滑板'},
            'Спальные мешки, коврики, матрасы': {'de': 'Schlafsäcke, Isomatten, Matratzen', 'zh': '睡袋，垫子，床垫'},
            'Спортивное питание и косметика': {'de': 'Sportnahrung und Kosmetik', 'zh': '运动营养和化妆品'},
            'Страйкбол': {'de': 'Airsoft', 'zh': '模拟战'},
            'Танцы': {'de': 'Tanz', 'zh': '舞蹈'},
            'Теннис': {'de': 'Tennis', 'zh': '网球'},
            'Тренажеры': {'de': 'Fitnessgeräte', 'zh': '健身器材'},
            'Туризм': {'de': 'Tourismus', 'zh': '旅游'},
            'Туристические аксессуары': {'de': 'Reisezubehör', 'zh': '旅游配件'},
            'Тяжелая атлетика': {'de': 'Gewichtheben', 'zh': '举重'},
            'Фитнес': {'de': 'Fitness', 'zh': '健身'},
            'Ходьба': {'de': 'Gehen', 'zh': '步行'},
            'Экипировка': {'de': 'Ausrüstung', 'zh': '装备'},
            'Электроника и навигация': {'de': 'Elektronik und Navigation', 'zh': '电子和导航'},
            'Аксессуары': {'de': 'Accessoires', 'zh': '配饰'},
            'Волосы': {'de': 'Haare', 'zh': '头发'},
            'Дермокосметика': {'de': 'Dermokosmetik', 'zh': '皮肤化妆品'},
            'Детская декоративная косметика': {'de': 'Kinder-Dekorativkosmetik', 'zh': '儿童装饰化妆品'},
            'Для загара': {'de': 'Für die Bräune', 'zh': '晒黑用品'},
            'Для мам и малышей': {'de': 'Für Mütter und Babys', 'zh': '为妈妈和宝宝'},
            'Израильская косметика': {'de': 'Israelische Kosmetik', 'zh': '以色列化妆品'},
            'Инструменты для парикмахеров': {'de': 'Werkzeuge für Friseure', 'zh': '理发工具'},
            'Корейские бренды': {'de': 'Koreanische Marken', 'zh': '韩国品牌'},
            'Косметические аппараты и аксессуары': {'de': 'Kosmetikgeräte und Zubehör', 'zh': '化妆仪器和配件'},
            'Макияж': {'de': 'Make-up', 'zh': '化妆'},
            'Мужская линия': {'de': 'Männerlinie', 'zh': '男士系列'},
            'Ногти': {'de': 'Nägel', 'zh': '指甲'},
            'Органическая косметика': {'de': 'Organische Kosmetik', 'zh': '有机化妆品'},
            'Парфюмерия': {'de': 'Parfüm', 'zh': '香水'},
            'Подарочные наборы': {'de': 'Geschenksets', 'zh': '礼品套装'},
            'Профессиональная косметика': {'de': 'Professionelle Kosmetik', 'zh': '专业化妆品'},
            'Средства личной гигиены': {'de': 'Mittel zur persönlichen Hygiene', 'zh': '个人卫生用品'},
            'Гигиена полости рта': {'de': 'Mundhygiene', 'zh': '口腔卫生'},
            'Уход за кожей': {'de': 'Hautpflege', 'zh': '护肤'},
            'Интимная гигиена': {'de': 'Intimhygiene', 'zh': '私密卫生'},
            'Для ванны и душа': {'de': 'Für Bad und Dusche', 'zh': '沐浴用品'},
            'Гель-лаки': {'de': 'Gel-Lacke', 'zh': '凝胶指甲油'},
            'Дезинфекция и антисептика': {'de': 'Desinfektion und Antiseptika', 'zh': '消毒和抗菌'},
            'Для снятия лака': {'de': 'Zum Entfernen von Lack', 'zh': '卸甲用品'},
            'Лаки': {'de': 'Lacke', 'zh': '指甲油'},
            'Наборы': {'de': 'Sets', 'zh': '套装'},
            'Накладные ногти и декор': {'de': 'Kunstnägel und Dekor', 'zh': '假指甲和装饰'},
            'Уход за ногтями': {'de': 'Nagelpflege', 'zh': '指甲护理'},
            'Для роста волос': {'de': 'Für das Haarwachstum', 'zh': '促进头发生长'},
            'Наращивание волос': {'de': 'Haarverlängerung', 'zh': '接发'},
            'Окрашивание волос и химическая завивка': {'de': 'Haarfärbung und chemische Dauerwelle', 'zh': '染发和化学烫发'},
            'Стайлинг': {'de': 'Styling', 'zh': '造型'},
            'Уход за волосами': {'de': 'Haarpflege', 'zh': '头发护理'},
            'Шампуни и кондиционеры': {'de': 'Shampoos und Conditioner', 'zh': '洗发水和护发素'},
            'Антистресс': {'de': 'Antistress', 'zh': '抗压'},
            'Для малышей': {'de': 'Für Babys', 'zh': '婴儿用品'},
            'Для песочницы': {'de': 'Für den Sandkasten', 'zh': '沙盘玩具'},
            'Игровые комплексы': {'de': 'Spielkomplexe', 'zh': '游戏套装'},
            'Игровые наборы': {'de': 'Spielsets', 'zh': '游戏组合'},
            'Игрушечный транспорт': {'de': 'Spielzeugtransport', 'zh': '玩具交通工具'},
            'Игрушки для ванной': {'de': 'Badespielzeug', 'zh': '浴室玩具'},
            'Интерактивные': {'de': 'Interaktive', 'zh': '互动'},
            'Кинетический песок': {'de': 'Kinetischer Sand', 'zh': '动感沙'},
            'Конструкторы': {'de': 'Konstruktoren', 'zh': '积木'},
            'Куклы и аксессуары': {'de': 'Puppen und Zubehör', 'zh': '娃娃和配件'},
            'Музыкальные': {'de': 'Musikalisch', 'zh': '音乐'},
            'Мыльные пузыри': {'de': 'Seifenblasen', 'zh': '肥皂泡'},
            'Мягкие игрушки': {'de': 'Weiche Spielzeuge', 'zh': '软玩具'},
            'Наборы для опытов': {'de': 'Experimentierkästen', 'zh': '实验套装'},
            'Настольные игры': {'de': 'Brettspiele', 'zh': '桌游'},
            'Радиоуправляемые': {'de': 'Ferngesteuerte', 'zh': '遥控'},
            'Развивающие игрушки': {'de': 'Entwicklungsspielzeug', 'zh': '启蒙玩具'},
            'Сборные модели': {'de': 'Modelle zum Zusammenbauen', 'zh': '拼装模型'},
            'Спортивные игры': {'de': 'Sportspiele', 'zh': '体育游戏'},
            'Сюжетно-ролевые игры': {'de': 'Rollenspiele', 'zh': '角色扮演游戏'},
            'Творчество и рукоделие': {'de': 'Kreativität und Basteln', 'zh': '创意与手工艺'},
            'Фигурки и роботы': {'de': 'Figuren und Roboter', 'zh': '人物和机器人'}
        }

        for original_name, translations in name_translations.items():
            try:
                # Use filter() instead of get() to handle potential multiple results
                items = ItemSubcategory.objects.filter(name_ru=original_name)

                for item in items:
                    activate('de')
                    item.name = translations.get('de', original_name)
                    item.save()

                    activate('zh')
                    item.name = translations.get('zh', original_name)
                    item.save()

                    # Switch back to the default language
                    activate('en')

            except ItemSubcategory.DoesNotExist:
                print(f"ItemSubcategory with name '{original_name}' does not exist.")
                continue

        return Response(data={'message': _('Translations added successfully')}, status=status.HTTP_200_OK)
