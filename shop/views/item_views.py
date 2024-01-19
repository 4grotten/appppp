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
            'Ботфорты': {'de': 'Stiefel', 'zh': '靴子'},
            'Стейки': {'de': 'Steaks', 'zh': '牛排'},
            'Обжаренные роллы': {'de': 'Gebratene Rollen', 'zh': '炸卷'},
            'Экскурсии': {'de': 'Ausflüge', 'zh': '旅行'},
            'Кутабы': {'de': 'Kutaby', 'zh': '库塔比（阿塞拜疆煎饼）'},
            'Маринады': {'de': 'Marinaden', 'zh': '腌制料'},
            'Обязательно знать ⚠️': {'de': 'Unbedingt wissen ⚠️', 'zh': '务必了解 ⚠️'},
            'Signature Milky Jar Drinks': {'de': 'Signature Milky Jar Drinks', 'zh': '招牌牛奶罐饮品'},
            'SINGLE MALT 🥃': {'de': 'SINGLE MALT 🥃', 'zh': '单一麦芽威士忌 🥃'},
            'Пальто': {'de': 'Mantel', 'zh': '外套'},
            'Бразильская кухня': {'de': 'Brasilianische Küche', 'zh': '巴西菜'},
            'Онлайн треннинг': {'de': 'Online-Training', 'zh': '在线培训'},
            'Рыба и морепродукты/Fish and seafood': {'de': 'Fisch und Meeresfrüchte', 'zh': '鱼和海鲜'},
            'Вязаная одежда': {'de': 'Gestrickte Kleidung', 'zh': '针织衣物'},
            'Плед': {'de': 'Decke', 'zh': '毯子'},
            'Причёски': {'de': 'Frisuren', 'zh': '发型'},
            'Колбаски': {'de': 'Würstchen', 'zh': '香肠'},
            'Десерты': {'de': 'Desserts', 'zh': '甜点'},
            'Блюда из рыбы и морепродуктов': {'de': 'Fisch- und Meeresfrüchtegerichte', 'zh': '鱼和海鲜菜'},
            'Подставки под горячее': {'de': 'Untersetzer für heißes Geschirr', 'zh': '热菜垫'},
            'Милкшейки': {'de': 'Milchshakes', 'zh': '奶昔'},
            'Wine🍷': {'de': 'Wein🍷', 'zh': '葡萄酒🍷'},
            'Гарниры и соусы': {'de': 'Beilagen und Saucen', 'zh': '配菜和酱料'},
            'Для животных': {'de': 'Für Tiere', 'zh': '为动物'},
            'Фаст-Фуд': {'de': 'Fast Food', 'zh': '快餐'},
            'Аугментация подбородка 😻': {'de': 'Kinnaugmentation 😻', 'zh': '下巴增强 😻'},
            'Маринад на вынос': {'de': 'Marinade zum Mitnehmen', 'zh': '外带腌制料'},
            'Сладкие завтраки': {'de': 'Süße Frühstücke', 'zh': '甜早餐'},
            'Сноубутсы': {'de': 'Snowboots', 'zh': '雪地靴'},
            'Товары для курения': {'de': 'Raucherwaren', 'zh': '吸烟用品'},
            'Коврики для сушки посуды': {'de': 'Abtropfmatten für Geschirr', 'zh': '厨具晾干垫'},
            'Осень🍁🌤️': {'de': 'Herbst🍁🌤️', 'zh': '秋天🍁🌤️'},
            'Бренды, товарные знаки, авторские права': {'de': 'Marken, Markenzeichen, Urheberrechte', 'zh': '品牌、商标、版权'},
            'Кесадилья': {'de': 'Quesadilla', 'zh': '奎萨迪亚（墨西哥煎饼）'},
            'Фирменные брускетты': {'de': 'Hausgemachte Bruschetta', 'zh': '招牌意式烤面包片'},
            'Конверты': {'de': 'Umschläge', 'zh': '信封'},
            'Для одежды и мебели': {'de': 'Für Kleidung und Möbel', 'zh': '衣服和家具用品'},
            'Ром': {'de': 'Rum', 'zh': '朗姆酒'},
            'Вишневые помидоры свежие и органические': {'de': 'Frische Bio-Kirschpomodori', 'zh': '新鲜有机樱桃番茄'},
            'PowerBANK и Колонки': {'de': 'PowerBANK und Lautsprecher', 'zh': '移动电源和扬声器'},
            'Wok': {'de': 'Wok', 'zh': '炒锅'},
            'Сюжетно ролевые игры': {'de': 'Rollenspiele', 'zh': '故事角色扮演游戏'},
            'Насадки для швабр': {'de': 'Mop-Aufsätze', 'zh': '拖把头'},
            'Европейские горячие блюда': {'de': 'Europäische warme Gerichte', 'zh': '欧洲热菜'},
            'Поло футболки': {'de': 'Poloshirts', 'zh': 'POLO衫'},
            'Wow Strategy': {'de': 'Wow-Strategie', 'zh': '哇战略'},
            'Домашняя одежда': {'de': 'Hauskleidung', 'zh': '家居服'},
            'Салат в лаваше': {'de': 'Lavash-Salat', 'zh': '薄饼沙拉'},
            'ТУРЫ': {'de': 'Touren', 'zh': '旅行'},
            'Signature Hot Choco': {'de': 'Signature Hot Choco', 'zh': '招牌热巧克力'},
            'Номера': {'de': 'Zimmer', 'zh': '房间'},
            'Плов': {'de': 'Plov (Reisgericht)', 'zh': '普洛夫（米饭菜）'},
            '-20%': {'de': '-20%', 'zh': '-20%'},
            'Изделия из теста': {'de': 'Teigwaren', 'zh': '面点'},
            'Рыба': {'de': 'Fisch', 'zh': '鱼'},
            'Феромоны': {'de': 'Pheromone', 'zh': '信息素'},
            'Пицца половинки': {'de': 'Pizza-Hälften', 'zh': '比萨半份'},
            'Пельмешки и варенички от Тесто Место': {'de': 'Pelmeni und Vareniki von Teigplatz',
                                                     'zh': 'Dough Place的饺子和馅饼'},
            'Street Food': {'de': 'Street Food', 'zh': '街头食品'},
            'Суши и Роллы': {'de': 'Sushi und Rollen', 'zh': '寿司和卷'},
            'Wines from Italy': {'de': 'Weine aus Italien', 'zh': '意大利葡萄酒'},
            'Десерт': {'de': 'Dessert', 'zh': '甜点'},
            'Спортивная одежда': {'de': 'Sportkleidung', 'zh': '运动服'},
            'Искусство': {'de': 'Kunst', 'zh': '艺术'},
            'Барсетки': {'de': 'Brieftaschen', 'zh': '小钱包'},
            'Блюда для большой компании': {'de': 'Gerichte für große Gruppen', 'zh': '适合大团体的菜'},
            'Виды услуг': {'de': 'Dienstleistungen', 'zh': '服务种类'},
            'Замороженная пельмени': {'de': 'Gefrorene Pelmeni', 'zh': '冷冻饺子'},
            'К чаю': {'de': 'Zum Tee', 'zh': '茶点'},
            'Лонгрид': {'de': 'Longrid', 'zh': '龙肉'},
            'PROMOTION (COOLERS) 🍹': {'de': 'PROMOTION (COOLERS) 🍹', 'zh': '促销（冷饮）🍹'},
            'Американская кухня': {'de': 'Amerikanische Küche', 'zh': '美国菜'},
            'Биркенштоки': {'de': 'Birkenstock', 'zh': '波肯斯多克'},
            'Концерт': {'de': 'Konzert', 'zh': '音乐会'},
            'Информация': {'de': 'Information', 'zh': '信息'},
            'MAINS 🥘': {'de': 'Hauptgerichte 🥘', 'zh': '主菜 🥘'},
            'BURGERS 🍔': {'de': 'Burger 🍔', 'zh': '汉堡 🍔'},
            'Коврики для ванной': {'de': 'Badematten', 'zh': '浴室垫'},
            'Ночник': {'de': 'Nachtlampe', 'zh': '小夜灯'},
            'Видео урок': {'de': 'Video-Lektion', 'zh': '视频教程'},
            'Мучные изделия': {'de': 'Mehlprodukte', 'zh': '面制品'},
            'Лазерное оборудование': {'de': 'Lasergeräte', 'zh': '激光设备'},
            'CHAMPAGNE & SPARKLING 🍾': {'de': 'Champagner & Perlwein 🍾', 'zh': '香槟和起泡酒 🍾'},
            'Увеличение губ 💋': {'de': 'Lippenvergrößerung 💋', 'zh': '嘴唇增大 💋'},
            'Изображение просмотр': {'de': 'Bildansicht', 'zh': '图片查看'},
            "Coffee & Tea Lover's Page": {'de': 'Kaffee- und Teeliebhaberseite', 'zh': '咖啡和茶爱好者页面'},
            'Филлеры 💊': {'de': 'Füllstoffe 💊', 'zh': '填充剂 💊'},
            'Акция': {'de': 'Aktion', 'zh': '活动'},
            'Студия': {'de': 'Studio', 'zh': '工作室'},
            'Консультация психолога': {'de': 'Psychologische Beratung', 'zh': '心理咨询'},
            'Китайская кухня': {'de': 'Chinesische Küche', 'zh': '中国菜'},
            'Фургон': {'de': 'Lieferwagen', 'zh': '货车'},
            'Мыло и шампуни': {'de': 'Seifen und Shampoos', 'zh': '肥皂和洗发水'},
            'Перманентный макияж бровей': {'de': 'Permanent Make-up für Augenbrauen', 'zh': '永久性眉毛化妆'},
            'Балетки': {'de': 'Ballettschuhe', 'zh': '芭蕾舞鞋'},
            'Клиники': {'de': 'Kliniken', 'zh': '诊所'},
            'Карак чай': {'de': 'Karak-Tee', 'zh': '喀喇喀茶'},
            'Салаты на вынос': {'de': 'Salate zum Mitnehmen', 'zh': '外卖沙拉'},
            'Лнр': {'de': 'LNR', 'zh': '卢甘斯克人民共和国'},
            'Спагетти (Аль Денте)': {'de': 'Spaghetti (al dente)', 'zh': '意大利面（有嚼劲）'},
            'Цветы': {'de': 'Blumen', 'zh': '花卉'},
            'Улучшенный': {'de': 'Verbessert', 'zh': '改进的'},
            'Завтраки с 11 до 13': {'de': 'Frühstück von 11 bis 13 Uhr', 'zh': '11点到13点早餐'},
            'Рыба и морепродукты': {'de': 'Fisch und Meeresfrüchte', 'zh': '鱼和海鲜'},
            'Косметички , ЭКО мешочки': {'de': 'Kosmetiktaschen, ECO-Taschen', 'zh': '化妆包，环保袋'},
            'Нити до и после 🤩': {'de': 'Fäden vorher und nachher 🤩', 'zh': '前后的线 🤩'},
            'PROMOTION  (WATERMELON) 🍸': {'de': 'WERBUNG (WASSERMELONE) 🍸', 'zh': '促销（西瓜）🍸'},
            'Эспадрильи': {'de': 'Espadrilles', 'zh': '搏台'},
            'Одежда Зима': {'de': 'Winterkleidung', 'zh': '冬季服装'},
            'Детям': {'de': 'Für Kinder', 'zh': '给孩子们'},
            'Досуг и информация': {'de': 'Freizeit und Information', 'zh': '娱乐和信息'},
            'Азербайджанская кухня': {'de': 'Aserbaidschanische Küche', 'zh': '阿塞拜疆菜'},
            'Холодные роллы': {'de': 'Kalte Rollen', 'zh': '冷卷'},
            'Сандалии': {'de': 'Sandalen', 'zh': '凉鞋'},
            'Лапша,паста': {'de': 'Nudeln, Pasta', 'zh': '面条，意大利面'},
            'Стейк и рыба': {'de': 'Steak und Fisch', 'zh': '牛排和鱼'},
            'Салфетки для оптики': {'de': 'Tücher für Optik', 'zh': '光学纸巾'},
            'Кроссовки Бона': {'de': 'Bona Sneakers', 'zh': '宝纳运动鞋'},
            'Прайс Лист': {'de': 'Preisliste', 'zh': '价目表'},
            'Кроссовки': {'de': 'Sneakers', 'zh': '运动鞋'},
            'Фирменные блюда из рыбы': {'de': 'Markengerichte aus Fisch', 'zh': '品牌鱼菜'},
            'Запеченные Роллы': {'de': 'Gebackene Rollen', 'zh': '烤卷'},
            'Фигурки из ароматических смол': {'de': 'Figuren aus aromatischem Harz', 'zh': '香脂雕像'},
            'Холодный кофе': {'de': 'Eiskaffee', 'zh': '冷咖啡'},
            'Бизнес ланч': {'de': 'Business-Lunch', 'zh': '商务午餐'},
            'Тематические шарики': {'de': 'Thematische Bälle', 'zh': '主题球'},
            'Новые блюда': {'de': 'Neue Gerichte', 'zh': '新菜'},
            'Uehfhdhdhdhdhxbxbbxsjskaanvfnxkzosjehfjcjdhsbsbdhxjxdjkdkslsla': {
                'de': 'Uehfhdhdhdhdhxbxbbxsjskaanvfnxkzosjehfjcjdhsbsbdhxjxdjkdkslsla',
                'zh': 'Uehfhdhdhdhdhxbxbbxsjskaanvfnxkzosjehfjcjdhsbsbdhxjxdjkdkslsla'},
            'Азиатская кухня': {'de': 'Asiatische Küche', 'zh': '亚洲菜'},
            'Крышки': {'de': 'Abdeckungen', 'zh': '盖子'},
            'Нижнее белье': {'de': 'Unterwäsche', 'zh': '内衣'},
            'Русская кухня': {'de': 'Russische Küche', 'zh': '俄罗斯菜'},
            'Мудрость': {'de': 'Weisheit', 'zh': '智慧'},
            'Замороженные вареники': {'de': 'Gefrorene Wareniki', 'zh': '冷冻水饺'},
            'Новинки': {'de': 'Neuheiten', 'zh': '新品'},
            'Уйгурская кухня': {'de': 'Uigurische Küche', 'zh': '维吾尔菜'},
            'Паназиатская кухня': {'de': 'Panasiatische Küche', 'zh': '泛亚洲菜'},
            'Соусы': {'de': 'Soßen', 'zh': '酱汁'},
            'Слайм и все для слайма': {'de': 'Schleim und alles für den Schleim', 'zh': '黏土和所有黏土用品'},
            'Аксессуары': {'de': 'Accessoires', 'zh': '配饰'},
            'Слиперы': {'de': 'Hausschuhe', 'zh': '拖鞋'},
            'Коньяк': {'de': 'Cognac', 'zh': '干邑'},
            'Стейки/Барбекю/Гриль/Колбаски': {'de': 'Steaks/Barbecue/Grill/Würstchen', 'zh': '牛排/烧烤/烧烤/香肠'},
            'BLENDED 🥃': {'de': 'GEMISCHT 🥃', 'zh': '混合 🥃'},
            'Alcohol Menu': {'de': 'Alkoholkarte', 'zh': '酒水菜单'},
            'Оборудование для Эпиляции': {'de': 'Haarentfernungsgeräte', 'zh': '脱毛设备'},
            'Бургеры/Сэндвичи/Круассана/Панини/Роллы': {'de': 'Burger/Sandwiches/Croissants/Panini/Rolls',
                                                        'zh': '汉堡包/三明治/羊角面包/帕尼尼/卷'},
            'Европейская кухня': {'de': 'Europäische Küche', 'zh': '欧洲菜'},
            'Fresh Bakery by Saya': {'de': 'Frische Bäckerei von Saya', 'zh': 'Saya的新鲜面包店'},
            'Полезные завтраки': {'de': 'Gesunde Frühstücke', 'zh': '健康早餐'},
            'Новинки (только на Юнусалиева 101)': {'de': 'Neuheiten (nur in Yunusalieva 101)',
                                                   'zh': '新品（仅限Yunusalieva 101）'},
            'Концертый': {'de': 'Konzert', 'zh': '音乐会'},
            'Элитные авто': {'de': 'Luxusautos', 'zh': '豪华汽车'},
            'JUNK FOOD': {'de': 'JUNK FOOD', 'zh': '垃圾食品'},
            'Одеяло': {'de': 'Decke', 'zh': '毯子'},
            'Шапки': {'de': 'Hüte', 'zh': '帽子'},
            'Сланцы': {'de': 'Sandalen', 'zh': '凉鞋'},
            'Сэндвичи': {'de': 'Sandwiches', 'zh': '三明治'},
            'Ваши Вопросы и ответы 🏎️⁉️😊': {'de': 'Ihre Fragen und Antworten 🏎️⁉️😊', 'zh': '您的问题和答案 🏎️⁉️😊'},
            'Комплекс до и после 👑': {'de': 'Komplex vor und nach 👑', 'zh': '前后综合 👑'},
            'Гамбургеры': {'de': 'Hamburger', 'zh': '汉堡包'},
            'Голова': {'de': 'Kopf', 'zh': '头'},
            'Канабис марихуана и': {'de': 'Cannabis Marihuana und', 'zh': '大麻和大麻'},
            'Системы полива и орошения. Шланги.': {'de': 'Bewässerungs- und Beregnungssysteme. Schläuche.',
                                                   'zh': '灌溉和喷灌系统。软管。'},
            'Лакокрасочные материалы': {'de': 'Farben und Lacke', 'zh': '涂料和油漆材料'},
            'Вторые блюда-Корейская кухня': {'de': 'Zweite Gerichte - Koreanische Küche', 'zh': '第二道菜 - 韩国厨房'},
            'Двери, окна и фурнитура': {'de': 'Türen, Fenster und Beschläge', 'zh': '门窗和五金配件'},
            'Комплексные завтраки': {'de': 'Vollständige Frühstücke', 'zh': '综合早餐'},
            'Кофта': {'de': 'Strickjacke', 'zh': '羊毛衫'},
            'Лекция': {'de': 'Vorlesung', 'zh': '讲座'},
            'Фастфуд': {'de': 'Fast Food', 'zh': '快餐'},
            'Смузи': {'de': 'Smoothie', 'zh': '果汁冰沙'},
            'Цветные ножи с чехлом': {'de': 'Bunte Messer mit Hülle', 'zh': '带套的彩色刀'},
            'Ассорти шашлыков': {'de': 'Verschiedene Schaschlik-Spieße', 'zh': '各种串烧'},
            'Емкости для хранения': {'de': 'Aufbewahrungsbehälter', 'zh': '存储容器'},
            'Грузинская кухня': {'de': 'Georgische Küche', 'zh': '格鲁吉亚厨房'},
            'Пироги и торты на заказ': {'de': 'Kuchen und Torten auf Bestellung', 'zh': '定制馅饼和蛋糕'},
            'Фрукты': {'de': 'Obst', 'zh': '水果'},
            'Угги': {'de': 'Ugg-Boots', 'zh': '雪地靴'},
            'Котлетки домашние': {'de': 'Hausgemachte Frikadellen', 'zh': '自制肉饼'},
            'Офис продаж': {'de': 'Verkaufsbüro', 'zh': '销售办公室'},
            'Дополнительно': {'de': 'Zusätzlich', 'zh': '额外'},
            'Starters and Share': {'de': 'Vorspeisen und Teilen', 'zh': '开胃菜和分享'},
            'Мучные изделия и гарниры': {'de': 'Mehlprodukte und Beilagen', 'zh': '面食和配菜'},
            'Бизнес авто': {'de': 'Geschäftsauto', 'zh': '商务车'},
            'завтраки/breakfasts': {'de': 'Frühstücke', 'zh': '早餐'},
            'Грелки-игрушки': {'de': 'Heizspielzeug', 'zh': '加热玩具'},
            'Точилки для ножей': {'de': 'Messer-Schärfer', 'zh': '刀具磨刀器'},
            'Фирменные блюда из говядины': {'de': 'Markengerichte aus Rindfleisch', 'zh': '牛肉品牌菜'},
            'Water & Juices': {'de': 'Wasser & Säfte', 'zh': '水和果汁'},
            'Машинные аксессуары': {'de': 'Autozubehör', 'zh': '汽车配件'},
            'Майка': {'de': 'Tank Top', 'zh': '背心'},
            'Джоггеры': {'de': 'Jogginghose', 'zh': '慢跑裤'},
            'Горячие напитки': {'de': 'Heißgetränke', 'zh': '热饮'},
            'Пельмешки и варенички': {'de': 'Pelmeni und Wareniki', 'zh': '俄罗斯饺子和水饺'},
            'Оборудование для коррекции фигуры': {'de': 'Figurkorrektur-Ausrüstung', 'zh': '塑身器材'},
            'Галоши': {'de': 'Galoschen', 'zh': '胶鞋'},
            'Полотенца': {'de': 'Handtücher', 'zh': '毛巾'},
            'Добавки в бетон': {'de': 'Zusatzstoffe für Beton', 'zh': '混凝土添加剂'},
            'Секс -машина': {'de': 'Sexmaschine', 'zh': '性爱机器'},
            'Спортивные авто': {'de': 'Sportwagen', 'zh': '运动汽车'},
            'Еврейская кухня': {'de': 'Jüdische Küche', 'zh': '犹太菜'},
            'Топы': {'de': 'Oberteile', 'zh': '上衣'},
            'Батончики': {'de': 'Riegel', 'zh': '棒'},
            'Куртки': {'de': 'Jacken', 'zh': '夹克'},
            'Делюкс': {'de': 'Deluxe', 'zh': '豪华'},
            'Наборы ножей': {'de': 'Messer-Sets', 'zh': '刀具套装'},
            'Допы': {'de': 'Extras', 'zh': '附加项'},
            'Овощечистки и овощерезки': {'de': 'Gemüseschäler und -schneider', 'zh': '蔬菜削皮器和切菜器'},
            'Немецкие средства AMV': {'de': 'Deutsche Mittel AMV', 'zh': '德国AMV产品'},
            'Аминокислота': {'de': 'Aminosäure', 'zh': '氨基酸'},
            'Паста/Paste': {'de': 'Nudeln/Paste', 'zh': '面条/面糊'},
            'Горнолыжные костюмы': {'de': 'Skianzüge', 'zh': '滑雪服'},
            'Вок/Wok': {'de': 'Wok', 'zh': '炒锅'},
            'Теневая растушовка бровей': {'de': 'Brow Shading', 'zh': '眉毛晕染'},
            'Сексуальная кукла': {'de': 'Sexuelle Puppe', 'zh': '性爱娃娃'},
            'Силиконовые крышки': {'de': 'Silikonabdeckungen', 'zh': '硅胶盖子'},
            'Кавказский шашлык': {'de': 'Kaukasischer Schaschlik', 'zh': '高加索串烧'},
            'Аниме и брошки': {'de': 'Anime und Broschen', 'zh': '动漫和胸针'},
            'Одежда ДЕМИ': {'de': 'Kleidung DEMI', 'zh': 'DEMI服装'},
            'Шашлыки и блюда на мангале': {'de': 'Schaschlik und Grillgerichte', 'zh': '串烧和烤菜'},
            'Сеты': {'de': 'Sets', 'zh': '套装'},
            'Снэки': {'de': 'Snacks', 'zh': '零食'},
            'Полотенце': {'de': 'Handtuch', 'zh': '毛巾'},
            'Соусы/Хлеб': {'de': 'Soßen/Brot', 'zh': '酱料/面包'},
            'BBB': {'de': 'BBB', 'zh': 'BBB'},
            'Наполнители для риса': {'de': 'Reisfüllstoffe', 'zh': '米饭填料'},
            'Индийская кухня': {'de': 'Indische Küche', 'zh': '印度菜'},
            'Сеты для компании': {'de': 'Sets für Unternehmen', 'zh': '企业套装'},
            'Бизнес-ланчи ЧЕТВЕРГ': {'de': 'Business-Lunch Donnerstag', 'zh': '星期四商务午餐'},
            'Основные блюда': {'de': 'Hauptgerichte', 'zh': '主菜'},
            'Ремонт бетона': {'de': 'Betonreparatur', 'zh': '混凝土修复'},
            'Букеты цветов': {'de': 'Blumensträuße', 'zh': '花束'},
            'Пицца на традиционном тесте': {'de': 'Pizza auf traditionellem Teig', 'zh': '传统面饼披萨'},
            '100': {'de': '100', 'zh': '100'},
            'детей': {'de': 'Kinder', 'zh': '儿童'},
            'Вок': {'de': 'Wok', 'zh': '炒锅'},
            'Клея для теплоизоляционных плит': {'de': 'Kleber für Wärmedämmplatten', 'zh': '用于保温板的胶水'},
            'Клиника': {'de': 'Klinik', 'zh': '诊所'},
            'Герметик': {'de': 'Dichtungsmittel', 'zh': '密封剂'},
            'Поло': {'de': 'Polo', 'zh': 'POLO衫'},
            'Антипаста': {'de': 'Antipasti', 'zh': '开胃菜'},
            'Шарики цифры': {'de': 'Zahlenkugeln', 'zh': '数字球'},
            'Суши и роллы': {'de': 'Sushi und Rollen', 'zh': '寿司和卷'},
            'Жаровня': {'de': 'Bratpfanne', 'zh': '炸锅'},
            'Фут еда': {'de': 'Fußessen', 'zh': '足球食品'},
            'Продукты с говядиной': {'de': 'Rindfleischprodukte', 'zh': '牛肉制品'},
            'Я в Instagram как @barbershop_rich.': {'de': 'Ich bin auf Instagram als @barbershop_rich.',
                                                    'zh': '我在Instagram上的名字是@barbershop_rich。'},
            'Фирменные горячие блюда': {'de': 'Markengerichte', 'zh': '品牌热菜'},
            'Бибистандарты': {'de': 'Bibistandards', 'zh': '婴儿标准'},
            'Бюстгальтер': {'de': 'BH', 'zh': '文胸'},
            'Пробиотики': {'de': 'Probiotika', 'zh': '益生菌'},
            'Маркетинг': {'de': 'Marketing', 'zh': '营销'},
            'Я': {'de': 'Ich', 'zh': '我'},
            'Врачи и эксперты': {'de': 'Ärzte und Experten', 'zh': '医生和专家'},
            'Блюда для друзей': {'de': 'Gerichte für Freunde', 'zh': '朋友的菜'},
            'Пантолеты': {'de': 'Pantoletten', 'zh': '拖鞋'},
            'Hoodi': {'de': 'Kapuzenpulli', 'zh': '连帽衫'},
            'Соук Мезе': {'de': 'Souk Meze', 'zh': 'Souk Meze'},
            'Бургеры вегетарианские': {'de': 'Vegetarische Burger', 'zh': '素食汉堡'},
            'BOTTLE & CANNED 🍺': {'de': 'FLASCHE & DOSE 🍺', 'zh': '瓶装和罐装🍺'},
            'Пуховик': {'de': 'Daunenjacke', 'zh': '羽绒服'},
            'Пижамы': {'de': 'Pyjamas', 'zh': '睡衣'},
            'Комбинезоны и полукомбинезоны': {'de': 'Overalls und Halboveralls', 'zh': '连体服和半连体服'},
            'Супы и завтраки': {'de': 'Suppen und Frühstücke', 'zh': '汤和早餐'},
            'Ассорти': {'de': 'Sortiment', 'zh': '混合'},
            'Орешки и чипсы': {'de': 'Nüsse und Chips', 'zh': '坚果和薯片'},
            'Мямчь': {'de': 'Mjam', 'zh': '美味'},
            'Крылышки': {'de': 'Flügel', 'zh': '翅膀'},
            'Вопросы и ответы': {'de': 'Fragen und Antworten', 'zh': '问题和答案'},
            'Блюда в горшочках': {'de': 'Gerichte in Töpfchen', 'zh': '小锅菜'},
            'Блинчики': {'de': 'Pfannkuchen', 'zh': '薄煎饼'},
            'Вино': {'de': 'Wein', 'zh': '葡萄酒'},
            'Шарики из фольги': {'de': 'Folienkugeln', 'zh': '铝箔球'},
            'Лечебная омолаживающая космецевтика': {'de': 'Heilende verjüngende Kosmezeutik', 'zh': '治疗性护肤化妆品'},
            'Билеты': {'de': 'Tickets', 'zh': '门票'},
            'Starters': {'de': 'Vorspeisen', 'zh': '开胃菜'},
            'Coffee Page': {'de': 'Kaffeeseite', 'zh': '咖啡页'},
            'Бизнес ланч с 10-00 до 16-00': {'de': 'Business-Lunch von 10:00 bis 16:00 Uhr', 'zh': '10:00至16:00的商务午餐'},
            'Полуботинки': {'de': 'Halbschuhe', 'zh': '半鞋'},
            'Блюда из рыбы и курицы': {'de': 'Gerichte aus Fisch und Huhn', 'zh': '鱼和鸡的菜'},
            'Лоферы': {'de': 'Loafer', 'zh': '懒汉鞋'},
            'Курица \\ Рыба': {'de': 'Huhn \\ Fisch', 'zh': '鸡肉 \\ 鱼'},
            'Горячие закуски': {'de': 'Warme Vorspeisen', 'zh': '热前菜'},
            'Плащ': {'de': 'Mantel', 'zh': '斗篷'},
            'Гарниры': {'de': 'Beilagen', 'zh': '配菜'},
            'Стейки и шашлык': {'de': 'Steaks und Schaschlik', 'zh': '牛排和烤肉'},
            'Барбекю гриль': {'de': 'Barbecue-Grill', 'zh': '烧烤炉'},
            'Коньячный напиток': {'de': 'Cognac-Getränk', 'zh': '白兰地酒'},
            'Отделочные материалы---Декоративные краски': {'de': 'Veredelungsmaterialien - Dekorative Farben',
                                                           'zh': '装饰材料-装饰油漆'},
            'Приправа': {'de': 'Gewürz', 'zh': '调味品'},
            'Любителям бани': {'de': 'Für Saunafreunde', 'zh': '桑拿爱好者'},
            'Цветы в горшочках': {'de': 'Blumen in Töpfen', 'zh': '盆栽花卉'},
            'Мастер класс': {'de': 'Meisterklasse', 'zh': '大师课程'},
            'Антимоль серия Красный кедр': {'de': 'Mottenserie Roter Zeder', 'zh': '红雪松防虫系列'},
            'DRAFT BEER 🍻': {'de': 'ZAPFBIER 🍻', 'zh': '生啤酒🍻'},
            'Удаление': {'de': 'Entfernung', 'zh': '删除'},
            'TEA & COFFEE ☕️': {'de': 'TEE & KAFFEE ☕️', 'zh': '茶和咖啡☕️'},
            'Салаты и холодные закуски': {'de': 'Salate und kalte Vorspeisen', 'zh': '沙拉和冷盘'},
            'Бомберы': {'de': 'Bomberjacken', 'zh': '轰炸机夹克'},
            'Салфетки для авто': {'de': 'Auto-Servietten', 'zh': '汽车纸巾'},
            'Ручная лепка': {'de': 'Handmodellierung', 'zh': '手工塑造'},
            'Signature Cakes': {'de': 'Signature Cakes', 'zh': '招牌蛋糕'},
            'Блюда из баранины': {'de': 'Lammgerichte', 'zh': '羊肉菜'},
            'Блюда из рыбы': {'de': 'Fischgerichte', 'zh': '鱼菜'},
            'Банкетное меню': {'de': 'Bankettmenü', 'zh': '宴会菜单'},
            'Курочка': {'de': 'Hühnchen', 'zh': '小鸡'},
            'Блюда к белому вину': {'de': 'Gerichte zum weißen Wein', 'zh': '白葡萄酒菜'},
            'Разливное пиво': {'de': 'Fassbier', 'zh': '散装啤酒'},
            'Паста/Ризотто': {'de': 'Pasta/Risotto', 'zh': '意大利面/烩饭'},
            'Закуски': {'de': 'Snacks', 'zh': '小吃'},
            'Боулы поке': {'de': 'Poke-Schüsseln', 'zh': '波克碗'},
            'Батарейки': {'de': 'Batterien', 'zh': '电池'},
            'Блюда из требухи': {'de': 'Gerichte aus Innereien', 'zh': '内脏菜'},
            'Для взрослых': {'de': 'Für Erwachsene', 'zh': '成人用品'},
            'Доступ к личному офису': {'de': 'Zugang zum persönlichen Büro', 'zh': '访问个人办公室'},
            'Носик до и после 🤥': {'de': 'Nase vorher und nachher 🤥', 'zh': '🤥之前和之后的鼻子'},
            'IT оборудование': {'de': 'IT-Ausrüstung', 'zh': 'IT设备'},
            'Технологии, изобретения, научные труды': {'de': 'Technologien, Erfindungen, wissenschaftliche Arbeiten',
                                                       'zh': '技术，发明，科研工作'},
            'Соковыжималки': {'de': 'Saftpressen', 'zh': '榨汁机'},
            'Невеста': {'de': 'Braut', 'zh': '新娘'},
            'Улучшенный комфорт': {'de': 'Verbesserter Komfort', 'zh': '提升舒适度'},
            'Холодные блюда': {'de': 'Kalte Gerichte', 'zh': '凉菜'},
            "French Toast's": {'de': 'Armer Ritter', 'zh': '法国吐司'},
            'Европейская кухня.Вторые блюда': {'de': 'Europäische Küche. Hauptgerichte', 'zh': '欧洲菜。主菜'},
            'Луноходы': {'de': 'Mondfahrzeuge', 'zh': '月球车'},
            'Темпура роллы (горячие роллы)': {'de': 'Tempura-Rollen (heiße Rollen)', 'zh': '天妇罗卷（热卷）'},
            'Доли в интеллектуальной собственности (IP-Shares)': {
                'de': 'Beteiligungen am geistigen Eigentum (IP-Anteile)', 'zh': '知识产权份额'},
            'Блюда домашней кухни': {'de': 'Hausgemachte Gerichte', 'zh': '家常菜'},
            'Наставник': {'de': 'Mentor', 'zh': '导师'},
            'Улучшенный лайт': {'de': 'Verbessertes Licht', 'zh': '提升光线'},
            'Суси': {'de': 'Sushi', 'zh': '寿司'},
            'Швабры для пола': {'de': 'Wischtücher für den Boden', 'zh': '地板拖把'},
            'Армянская кухня': {'de': 'Armenische Küche', 'zh': '亚美尼亚菜'},
            'Горячие роллы': {'de': 'Heiße Rollen', 'zh': '热卷'},
            'Фирменные завтраки до 17:00': {'de': 'Firmenfrühstücke bis 17:00 Uhr', 'zh': '17:00前的特色早餐'},
            'Чикен роллы': {'de': 'Hähnchenrollen', 'zh': '鸡肉卷'},
            'ПОДАРОЧНЫЕ СЕРТИФИКАТЫ': {'de': 'Geschenkgutscheine', 'zh': '礼品券'},
            'Шарики гиганты': {'de': 'Riesige Bälle', 'zh': '巨大的球'},
            'Медицинские кабинеты': {'de': 'Medizinische Kabinen', 'zh': '医疗室'},
            'Овощные блюда': {'de': 'Gemüsegerichte', 'zh': '蔬菜菜肴'},
            'Декор и аксессуары': {'de': 'Dekor und Accessoires', 'zh': '装饰和配饰'},
            'Fast food': {'de': 'Schnellimbiss', 'zh': '快餐'},
            'Англ': {'de': 'Englisch', 'zh': '英语'},
            'Полу сапоги': {'de': 'Halbstiefel', 'zh': '短靴'},
            'Салаты с майонезом': {'de': 'Salate mit Mayonnaise', 'zh': '蛋黄酱沙拉'},
            'Котлеты': {'de': 'Koteletts', 'zh': '肉饼'},
            'Жилой комплекс': {'de': 'Wohnkomplex', 'zh': '居住区'},
            'Ганфаны': {'de': 'Ganfany', 'zh': '甘范'},
            'Signature Milky Jar': {'de': 'Unterschrift Milchglas', 'zh': '招牌牛奶罐'},
            'Табачные изделия': {'de': 'Tabakwaren', 'zh': '烟草制品'},
            'Косметические средства с пробиотиками': {'de': 'Kosmetika mit Probiotika', 'zh': '含益生菌的化妆品'},
            'К шашлыку': {'de': 'Zum Schaschlik', 'zh': '烤肉配菜'},
            'Блюда из курицы': {'de': 'Hühnchengerichte', 'zh': '鸡肉菜肴'},
            'Панамы': {'de': 'Panamas', 'zh': '巴拿马帽'},
            'Шлепанцы': {'de': 'Sandalen', 'zh': '拖鞋'},
            'Рубашки,сорочки,батники': {'de': 'Hemden, Blusen, Batniki', 'zh': '衬衫，女衬衫，巴特尼基'},
            'Жилые комплексы': {'de': 'Wohnkomplexe', 'zh': '住宅区'},
            'Для пола': {'de': 'Für den Boden', 'zh': '地板用品'},
            'Отделочные материалы---Декоративные покрытия': {'de': 'Veredelungsmaterialien - Dekorative Beschichtungen',
                                                             'zh': '装饰材料 - 装饰涂料'},
            'Итальянская кухня': {'de': 'Italienische Küche', 'zh': '意大利菜'},
            'Шарики': {'de': 'Bälle', 'zh': '小球'},
            'Процедуры 👩\u200d⚕️': {'de': 'Prozeduren 👩\u200d⚕️', 'zh': '程序 👩\u200d⚕️'},
            'Торты': {'de': 'Kuchen', 'zh': '蛋糕'},
            'Пиде': {'de': 'Pide', 'zh': '比达面包'},
            'Лагманы': {'de': 'Lagman', 'zh': '拉面'},
            'Колье и браслеты': {'de': 'Halsketten und Armbänder', 'zh': '项链和手链'},
            'Косметологические комбайны': {'de': 'Kosmetologische Kombinationen', 'zh': '美容仪器'},
            'Италия': {'de': 'Italien', 'zh': '意大利'},
            'Пицца на пышном тесте': {'de': 'Pizza mit dickem Teig', 'zh': '厚皮比萨'},
            'Боулы и закуски': {'de': 'Schalen und Snacks', 'zh': '碗和小吃'},
            'Предзаказ меню': {'de': 'Vorbestellmenü', 'zh': '预订菜单'},
            'Для тела': {'de': 'Für den Körper', 'zh': '身体护理'},
            'Для детей': {'de': 'Für Kinder', 'zh': '儿童用品'},
            'Футбол': {'de': 'Fußball', 'zh': '足球'},
            'Двери межкомнатные': {'de': 'Innentüren', 'zh': '室内门'},
            'Спортивные игры футбол , волейбол': {'de': 'Fußball- und Volleyballspiele', 'zh': '足球和排球比赛'},
            'Коммерческие помещения': {'de': 'Gewerbeflächen', 'zh': '商业空间'},
            'Мобильные и веб-приложения': {'de': 'Mobile und Webanwendungen', 'zh': '移动和Web应用'},
            'Китайская кухня/Горячие блюда': {'de': 'Chinesische Küche / Heiße Gerichte', 'zh': '中餐/热菜'},
            'Комбо': {'de': 'Kombination', 'zh': '套餐'},
            'Южнокорейская кухня': {'de': 'Südkoreanische Küche', 'zh': '韩国料理'},
            'Спортивные костюмы': {'de': 'Sportanzüge', 'zh': '运动套装'},
            'Эксклюзивная испанская косметика.': {'de': 'Exklusive spanische Kosmetik', 'zh': '独家西班牙化妆品'},
            'Брови': {'de': 'Augenbrauen', 'zh': '眉毛'},
            'АСД': {'de': 'ASD', 'zh': 'ASD'},
            'лосины': {'de': 'Leggings', 'zh': '紧身裤'},
            'Отделочные материалы---Венецианская декоративная штукатурка': {
                'de': 'Veredelungsmaterialien - Venezianischer dekorativer Putz', 'zh': '装饰材料 - 威尼斯装饰石膏'},
            'Морские животные': {'de': 'Meereslebewesen', 'zh': '海洋动物'},
            'Пицца': {'de': 'Pizza', 'zh': '比萨'},
            'Горячие блюда восточной кухни': {'de': 'Ostasiatische warme Gerichte', 'zh': '东方热菜'},
            'Ликёр': {'de': 'Likör', 'zh': '利口酒'},
            'Слип': {'de': 'Schlüpfer', 'zh': '内裤'},
            'Пита': {'de': 'Pita', 'zh': '皮塔'},
            'Электра Инструменты': {'de': 'Elektrowerkzeuge', 'zh': '电动工具'},
            'Кубинская кухня': {'de': 'Kubanische Küche', 'zh': '古巴菜'},
            'Косметики для домашнего ухода': {'de': 'Hautpflegekosmetik', 'zh': '家居护肤化妆品'},
            'Дневное Меню': {'de': 'Tagesmenü', 'zh': '日常菜单'},
            'Пироги': {'de': 'Kuchen', 'zh': '派'},
            'одежда Зима': {'de': 'Winterkleidung', 'zh': '冬季服装'},
            'Отделочные материалы---Фасадная штукатурка': {'de': 'Veredelungsmaterialien - Fassadenputz',
                                                           'zh': '装饰材料 - 外墙石膏'},
            'Покрывало': {'de': 'Bettdecke', 'zh': '床罩'},
            'Пикап': {'de': 'Pick-up', 'zh': '小货车'},
            'Национальная кухня': {'de': 'Nationale Küche', 'zh': '国家菜'},
            'Ребрышки': {'de': 'Rippchen', 'zh': '排骨'},
            'Виски купажированный': {'de': 'Verschnittener Whisky', 'zh': '混合威士忌'},
            'Халва': {'de': 'Halva', 'zh': '哈尔瓦'},
            'Губы': {'de': 'Lippen', 'zh': '嘴唇'},
            'Шаурма и пицца': {'de': 'Schawarma und Pizza', 'zh': '烤肉卷和比萨'},
            'Ризотто': {'de': 'Risotto', 'zh': '烩饭'},
            'Ребёнку': {'de': 'Kind', 'zh': '孩子'},
            'Стратегическая ссеия': {'de': 'Strategische Sitzung', 'zh': '战略会议'},
            'Произведения искусства, фотографии, видео': {'de': 'Kunstwerke, Fotos, Videos', 'zh': '艺术品，照片，视频'},
            'Цветы для вас': {'de': 'Blumen für dich', 'zh': '为您准备的花朵'},
            'Кальян': {'de': 'Shisha', 'zh': '水烟'},
            'Блюда из морепродуктов и рыбы': {'de': 'Gerichte aus Meeresfrüchten und Fisch', 'zh': '海鲜和鱼菜品'},
            'Блюда из овощей': {'de': 'Gemüsegerichte', 'zh': '素菜'},
            'Для любимых': {'de': 'Für die Liebsten', 'zh': '为亲爱的人'},
            'Ассорти на компанию': {'de': 'Gemischte Gesellschaft', 'zh': '混合拼盘'},
            'VODKA 🍸': {'de': 'Wodka', 'zh': '伏特加'},
            'Отделочные материалы---Декоративные добавки': {'de': 'Veredelungsmaterialien - Dekorative Zusätze',
                                                            'zh': '装饰材料 - 装饰性添加剂'},
            'Боул': {'de': 'Schale', 'zh': '碗'},
            'Изделия из курицы': {'de': 'Hühnerprodukte', 'zh': '鸡制品'},
            'Кофейные напитки': {'de': 'Kaffeegetränke', 'zh': '咖啡饮品'},
            'Халат': {'de': 'Bademantel', 'zh': '浴袍'},
            'Анальные игрушки': {'de': 'Analspielzeug', 'zh': '肛门玩具'},
            'Настойка': {'de': 'Aufguss', 'zh': '浸泡'},
            '1': {'de': '1', 'zh': '1'},
            'Лапша и Wok': {'de': 'Nudeln und Wok', 'zh': '面条和锅'},
            'Бизнес-ланчи ВТОРНИК': {'de': 'Business-Lunch am Dienstag', 'zh': '星期二的商务午餐'},
            'Мокасины': {'de': 'Mokassins', 'zh': '便鞋'},
            'Сэндвичи в хлебе': {'de': 'Brot-Sandwiches', 'zh': '面包三明治'},
            'Запеченые роллы': {'de': 'Gebackene Rollen', 'zh': '烤卷'},
            'Наши Услуги': {'de': 'Unsere Dienstleistungen', 'zh': '我们的服务'},
            'Универсальные салфетки': {'de': 'Universal-Tücher', 'zh': '通用抹布'},
            'MILKSHAKES & SMOOTHIES 🧋': {'de': 'MILCHSHAKES & SMOOTHIES', 'zh': '奶昔和冰沙'},
            'Недвижимость Аренда': {'de': 'Immobilienvermietung', 'zh': '房地产租赁'},
            'Блюда из тофу (соевого творога)': {'de': 'Gerichte mit Tofu', 'zh': '豆腐菜品'},
            'Треннинг': {'de': 'Training', 'zh': '培训'},
            'PIZZAS': {'de': 'PIZZAS', 'zh': '比萨'},
            'Ковры на каучуковой основе': {'de': 'Gummiunterlage Teppiche', 'zh': '橡胶底垫地毯'},
            'Седан': {'de': 'Limousine', 'zh': '轿车'},
            'Окрашивание волос': {'de': 'Haarfärbung', 'zh': '染发'},
            'PASTAS 🍝': {'de': 'PASTAS', 'zh': '意面'},
            'Бургеры стандартные': {'de': 'Standard-Burger', 'zh': '标准汉堡'},
            'Защитные перчатки для рук': {'de': 'Schutzhandschuhe', 'zh': '手部防护手套'},
            'Гунканы': {'de': 'Gunkans', 'zh': '蒲瓜寿司'},
            'Арабские блюда': {'de': 'Arabische Gerichte', 'zh': '阿拉伯菜'},
            'Блюда из морепродуктов и рыбы1': {'de': 'Gerichte aus Meeresfrüchten und Fisch1', 'zh': '海鲜和鱼菜品1'},
            'Домашняя кухня': {'de': 'Hausmannskost', 'zh': '家常菜'},
            'Завтраки🍳': {'de': 'Frühstücke', 'zh': '早餐'},
            'Greenfield': {'de': 'Greenfield', 'zh': '绿地'},
            'Тренеры 🏀': {'de': 'Trainer', 'zh': '教练'},
            'test': {'de': 'Test', 'zh': '测试'},
            'Команда 🏆': {'de': 'Team', 'zh': '团队'},
            'Напитки': {'de': 'Getränke', 'zh': '饮料'},
            'Холодные закуски': {'de': 'Kalte Vorspeisen', 'zh': '冷菜'},
            'Молочные продукты': {'de': 'Milchprodukte', 'zh': '乳制品'},
            'Выпечка': {'de': 'Backwaren', 'zh': '糕点'},
            'Абонемент 🤑': {'de': 'Abonnement 🤑', 'zh': '订阅 🤑'},
            'Завтраки2': {'de': 'Frühstücke2', 'zh': '早餐2'},
            'Степ-роллы': {'de': 'Step-Rolls', 'zh': 'Step-卷'},
            'Женская обувь': {'de': 'Damen Schuhe', 'zh': '女鞋'},
            'Безрукавка': {'de': 'Ärmellose Jacke', 'zh': '无袖外套'},
            'Блюда на заказ': {'de': 'Speisen auf Bestellung', 'zh': '定制菜品'},
            'Тренч': {'de': 'Trenchcoat', 'zh': '风衣'},
            'Main Dishes': {'de': 'Hauptgerichte', 'zh': '主菜'},
            'Сезонные блюда': {'de': 'Saisonale Gerichte', 'zh': '季节菜'},
            'Шашлыки': {'de': 'Schaschlik', 'zh': '烤肉串'},
            'Тефаль': {'de': 'Tefal', 'zh': '特福'},
            'Маки': {'de': 'Maki', 'zh': '卷寿司'},
            'Кофе черный': {'de': 'Schwarzer Kaffee', 'zh': '黑咖啡'},
            'V1TER': {'de': 'V1TER', 'zh': 'V1TER'},
            'Туфли': {'de': 'Schuhe', 'zh': '鞋'},
            'Сабо': {'de': 'Sabo', 'zh': '凉鞋'},
            'Шашлык': {'de': 'Schaschlik', 'zh': '烤肉串'},
            'Хачапури': {'de': 'Khachapuri', 'zh': '哈恰普里'},
            'Строй материалы': {'de': 'Bau Materialien', 'zh': '建筑材料'},
            'Восточные блюда': {'de': 'Orientalische Gerichte', 'zh': '东方美食'},
            'Кабриолет': {'de': 'Cabriolet', 'zh': '敞篷车'},
            'Ассорти роллы': {'de': 'Assorted Rolls', 'zh': '混合卷'},
            'Гидроизоляция': {'de': 'Abdichtung', 'zh': '防水'},
            'Для неё': {'de': 'Für sie', 'zh': '为她'},
            'Европейские блюда': {'de': 'Europäische Gerichte', 'zh': '欧洲美食'},
            'Neodim Laser': {'de': 'Neodim Laser', 'zh': 'Neodim Laser'},
            'На компанию': {'de': 'Für die Firma', 'zh': '公司用'},
            'Бургеры и сэндвичи': {'de': 'Burger und Sandwiches', 'zh': '汉堡和三明治'},
            'Косметика': {'de': 'Kosmetik', 'zh': '化妆品'},
            'Бренди': {'de': 'Brandy', 'zh': '白兰地'},
            'Купе': {'de': 'Coupé', 'zh': '轿跑车'},
            'Кофе': {'de': 'Kaffee', 'zh': '咖啡'},
            'Прохладительные напитки': {'de': 'Erfrischungsgetränke', 'zh': '凉饮'},
            'Спортивный костюм': {'de': 'Sportanzug', 'zh': '运动套装'},
            'Запечённые роллы': {'de': 'Gebackene Rollen', 'zh': '烤卷'},
            'Полотенца кухонные': {'de': 'Küchentücher', 'zh': '厨房毛巾'},
            'SOFT DRINKS 🥤': {'de': 'Erfrischungsgetränke 🥤', 'zh': '软饮料 🥤'},
            'Оборудование для индустрии красоты': {'de': 'Ausrüstung für die Schönheitsindustrie', 'zh': '美容行业设备'},
            'Блюда из фруктов': {'de': 'Fruchtgerichte', 'zh': '水果菜品'},
            'Установка оборудования': {'de': 'Ausrüstung installieren', 'zh': '设备安装'},
            'Бизнес-ланчи СРЕДА': {'de': 'Business-Lunch Mittwoch', 'zh': '周三商务午餐'},
            'Осень 🍁': {'de': 'Herbst 🍁', 'zh': '秋季 🍁'},
            'ADD-ONS 🥗': {'de': 'Zusatzprodukte 🥗', 'zh': '附加产品 🥗'},
            'Breakfast & Sweet Breakfast': {'de': 'Frühstück & süßes Frühstück', 'zh': '早餐和甜点早餐'},
            'JARDIN': {'de': 'Garten', 'zh': '花园'},
            'Шашлыки с 17-00 до 24-00 часов': {'de': 'Schaschlik von 17:00 bis 24:00 Uhr', 'zh': '烤肉串从17:00到24:00'},
            'Сумки для аксессуаров': {'de': 'Taschen für Accessoires', 'zh': '配饰袋'},
            'Шашлык по-азербайджански': {'de': 'Schaschlik auf Aserbaidschanisch', 'zh': '阿塞拜疆式烤肉串'},
            'Краски для перманентного макияжа': {'de': 'Permanent Make-up Farben', 'zh': '永久性化妆颜料'},
            'Услуги': {'de': 'Dienstleistungen', 'zh': '服务'},
            'Мангал меню': {'de': 'Grillmenü', 'zh': '烧烤菜单'},
            'Губки и щетки для посуды': {'de': 'Schwämme und Bürsten für Geschirr', 'zh': '洗碗用海绵和刷子'},
            'Промышленные полы': {'de': 'Industrieböden', 'zh': '工业地板'},
            'Проекты домов': {'de': 'Hausprojekte', 'zh': '房屋项目'},
            'Big Gathering Cakes': {'de': 'Große Versammlungskuchen', 'zh': '大聚会蛋糕'},
            'Блины': {'de': 'Pfannkuchen', 'zh': '薄煎饼'},
            'Эксклюзив': {'de': 'Exklusiv', 'zh': '独家'},
            'Двери': {'de': 'Türen', 'zh': '门'},
            'Педикюр': {'de': 'Pediküre', 'zh': '修脚'},
            'Жареные роллы': {'de': 'Gebratene Rollen', 'zh': '炸卷'},
            'Ножи специального назначения': {'de': 'Messer für besondere Verwendungszwecke', 'zh': '特殊用途刀具'},
            'Водка': {'de': 'Wodka', 'zh': '伏特加'},
            'Событие': {'de': 'Ereignis', 'zh': '事件'},
            'Роллы': {'de': 'Rollen', 'zh': '卷'},
            'Замороженные манты': {'de': 'Gefrorene Manti', 'zh': '冷冻馅饼'},
            'Фирменные блюда из баранины': {'de': 'Signature-Gerichte aus Lammfleisch', 'zh': '羊肉招牌菜'},
            'Черный кофе': {'de': 'Schwarzer Kaffee', 'zh': '黑咖啡'},
            'Стартеры/Соусы': {'de': 'Vorspeisen / Saucen', 'zh': '开胃菜/酱汁'},
            'Клей для плитки': {'de': 'Fliesenkleber', 'zh': '瓷砖胶'},
            'Завтрак 🍳': {'de': 'Frühstück 🍳', 'zh': '早餐 🍳'},
            'Открытки': {'de': 'Grußkarten', 'zh': '贺卡'},
            'Супы 🍜': {'de': 'Suppen 🍜', 'zh': '汤 🍜'},
            'Брови/ресницы': {'de': 'Augenbrauen/Wimpern', 'zh': '眉毛/睫毛'},
            'Правильное питание': {'de': 'Gesunde Ernährung', 'zh': '健康饮食'},
            'Блузки': {'de': 'Blusen', 'zh': '衬衫'},
            'Спецблюда': {'de': 'Spezialgerichte', 'zh': '特色菜'},
            'Мастурбатор': {'de': 'Masturbator', 'zh': '自慰器'},
            'Хлопушки': {'de': 'Poppers', 'zh': '鼻炸药'},
            'COCKTAILS 🍹': {'de': 'Cocktails 🍹', 'zh': '鸡尾酒 🍹'},
            'Аренда на ик': {'de': 'Vermietung von IK', 'zh': 'IK租赁'},
            'Side Dishes': {'de': 'Beilagen', 'zh': '配菜'},
            'Тест': {'de': 'Test', 'zh': '测试'},
            'Главные блюда': {'de': 'Hauptgerichte', 'zh': '主菜'},
            'Микроволокно для животных': {'de': 'Mikrofaser für Tiere', 'zh': '动物微纤维'},
            'Боди': {'de': 'Body', 'zh': '连体衣'},
            'Перекусы': {'de': 'Snacks', 'zh': '小吃'},
            'Основные блюда/Main dishes': {'de': 'Hauptgerichte', 'zh': '主菜'},
            'ВМЖ и ПМЖ': {'de': 'Auslandsaufenthalt und ständiger Wohnsitz', 'zh': '居住和永久居住'},
            'Tea Lovers': {'de': 'Teeliebhaber', 'zh': '茶爱好者'},
            'Wines from Spain': {'de': 'Weine aus Spanien', 'zh': '西班牙葡萄酒'},
            'Бизнес Ланч': {'de': 'Business-Lunch', 'zh': '商务午餐'},
            'Косметология': {'de': 'Kosmetologie', 'zh': '美容学'},
            'Супериор': {'de': 'Überlegen', 'zh': '高级'},
            'Китайская кухня/Баранина': {'de': 'Chinesische Küche/Lammfleisch', 'zh': '中餐/羊肉'},
            'пижама': {'de': 'Pyjama', 'zh': '睡衣'},
            'Мастурбатор тела': {'de': 'Körpermasturbator', 'zh': '身体自慰器'},
            'Горячие блюда на Josper': {'de': 'Heiße Gerichte auf Josper', 'zh': 'Josper热菜'},
            'Брюки': {'de': 'Hosen', 'zh': '裤子'},
            'Для дома': {'de': 'Für zu Hause', 'zh': '家居'},
            'Ковры на ПВХ-основе (спагетти)': {'de': 'Teppiche auf PVC-Basis (Spaghetti)', 'zh': 'PVC基地地毯（意大利面）'},
            'Coffee by Saya': {'de': 'Kaffee von Saya', 'zh': 'Saya咖啡'},
            'RED WINE 🍷': {'de': 'ROTWEIN 🍷', 'zh': '红酒 🍷'},
            'Тюрбаны': {'de': 'Turban', 'zh': '头巾'},
            'Пиротехника': {'de': 'Pyrotechnik', 'zh': '烟花爆竹'},
            'Afternoon Tea by Saya': {'de': 'Nachmittagstee von Saya', 'zh': 'Saya的下午茶'},
            'Вибратор': {'de': 'Vibrator', 'zh': '震动器'},
            'Курсы обучения': {'de': 'Ausbildungskurse', 'zh': '培训课程'},
            'Керамогранит': {'de': 'Feinsteinzeug', 'zh': '陶瓷花岗岩'},
            'Горячие блюда европейской кухни': {'de': 'Heiße Gerichte der europäischen Küche', 'zh': '欧洲菜的热菜'},
            'MOCKTAILS 🧋': {'de': 'MOCKTAILS 🧋', 'zh': '无酒精鸡尾酒 🧋'},
            'Морепродукты': {'de': 'Meeresfrüchte', 'zh': '海鲜'},
            'Губная помада': {'de': 'Lippenstift', 'zh': '唇膏'},
            'Куриная продукция': {'de': 'Hühnerprodukte', 'zh': '鸡产品'},
            'Бургер + картофель по-деревенски': {'de': 'Burger + Bauernkartoffeln', 'zh': '汉堡包 + 乡村土豆'},
            'Для массажа': {'de': 'Für die Massage', 'zh': '按摩用品'},
            'Тандырный шашлык': {'de': 'Tandyr Schaschlik', 'zh': '坦杜尔烤肉'},
            'Основное': {'de': 'Hauptgericht', 'zh': '主菜'},
            'Лимонады': {'de': 'Limonaden', 'zh': '柠檬水'},
            'Мексиканская кухня': {'de': 'Mexikanische Küche', 'zh': '墨西哥菜'},
            'Туры': {'de': 'Touren', 'zh': '旅游'},
            'Профессиональные': {'de': 'Professionell', 'zh': '专业'},
            'Угловой номер': {'de': 'Eckzimmer', 'zh': '角落房'},
            'Блюда из печи': {'de': 'Ofengerichte', 'zh': '烤菜'},
            'Армянский шашлык на открытом огне': {'de': 'Armenischer Schaschlik am offenen Feuer', 'zh': '亚美尼亚烤肉'},
            'Wok лапша': {'de': 'Wok-Nudeln', 'zh': '炒面'},
            'Tea Lovers Page': {'de': 'Teeliebhaberseite', 'zh': '茶爱好者页面'},
            'Помпы': {'de': 'Pumpen', 'zh': '泵'},
            'Декоративные штукатурки': {'de': 'Dekorative Putze', 'zh': '装饰性灰泥'},
            'Открывашки': {'de': 'Flaschenöffner', 'zh': '开瓶器'},
            'Курс оффлайн': {'de': 'Offline-Kurs', 'zh': '线下课程'},
            'Зимняя!': {'de': 'Winterlich!', 'zh': '冬季！'},
            'Аргентинская кухня': {'de': 'Argentinische Küche', 'zh': '阿根廷菜'},
            'KIDS MENU 🍭': {'de': 'Kinderkarte 🍭', 'zh': '儿童菜单 🍭'},
            'Пиде и пиццы': {'de': 'Pide und Pizza', 'zh': '比达和比萨'},
            'Ринопластика 👃': {'de': 'Rhinoplastik 👃', 'zh': '鼻整形 👃'},
            'Студия дизайн интерьера!': {'de': 'Innenarchitektur-Designstudio!', 'zh': '室内设计工作室！'},
            'Бириани': {'de': 'Biryani', 'zh': '比尔扬尼'},
            'Шашлык в тандыре': {'de': 'Schaschlik im Tandyr', 'zh': '坦杜尔烤肉'},
            'Онлайн курс': {'de': 'Online-Kurs', 'zh': '在线课程'},
            'Восточная кухня': {'de': 'Ostasiatische Küche', 'zh': '东方菜'},
            'Маринад': {'de': 'Marinade', 'zh': '腌料'},
            'Мансардные окна': {'de': 'Dachfenster', 'zh': '阁楼窗户'},
            'Препараты': {'de': 'Präparate', 'zh': '制剂'},
            'Кастрюли': {'de': 'Töpfe', 'zh': '锅'},
            'Для него': {'de': 'Für ihn', 'zh': '为他'},
            'Костюмы и комплекты': {'de': 'Anzüge und Sets', 'zh': '套装和套装'},
            'Фаст Фуд': {'de': 'Fast Food', 'zh': '快餐'},
            'HAPPY HOUR SPIRITS 🍸': {'de': 'HAPPY HOUR SPIRITS 🍸', 'zh': '欢乐时光烈酒 🍸'},
            'Крем для тела': {'de': 'Körperlotion', 'zh': '身体乳液'},
            'Боллы': {'de': 'Bolly', 'zh': 'Bolly'},
            'Турецкая кухня': {'de': 'Türkische Küche', 'zh': '土耳其菜'},
            'Жареные колбаски': {'de': 'Gebratene Würstchen', 'zh': '炸香肠'},
            'Бар': {'de': 'Bar', 'zh': '酒吧'},
            'Нити': {'de': 'Fäden', 'zh': '线'},
            'Наклейки': {'de': 'Aufkleber', 'zh': '贴纸'},
            'Бизнес-ланчи с 12-00 до 15-00': {'de': 'Business-Lunch von 12:00 bis 15:00 Uhr', 'zh': '12:00至15:00的商务午餐'},
            'Strap': {'de': 'Riemen', 'zh': '带'},
            'Вок/Тяхан': {'de': 'Wok/Tjahan', 'zh': '炒锅/特汉'},
            'Бублики': {'de': 'Bubliki', 'zh': '椰圈'},
            'BRANDY / COGNAC 🥃': {'de': 'BRANDY / COGNAC 🥃', 'zh': '白兰地/干邑 🥃'},
            'Лосины': {'de': 'Leggings', 'zh': '裤袜'},
            'Меню': {'de': 'Menü', 'zh': '菜单'},
            'К пиву': {'de': 'Bierbegleitung', 'zh': '搭配啤酒'},
            'Утюги': {'de': 'Bügeleisen', 'zh': '熨斗'},
            'Мыло': {'de': 'Seife', 'zh': '肥皂'},
            'TeSS': {'de': 'TeSS', 'zh': 'TeSS'},  # Assuming it's a proper noun without direct translation
            'Блюда из говядины': {'de': 'Rindfleischgerichte', 'zh': '牛肉菜品'},
            'Тосты': {'de': 'Toast', 'zh': '吐司'},
            'Услуги 📑': {'de': 'Dienstleistungen 📑', 'zh': '服务 📑'},
            'Блюда на жаровне и в горшочке': {'de': 'Gerichte auf dem Grill und im Topf', 'zh': '烤盘和砂锅菜品'},
            'Ифтарное меню': {'de': 'Iftar-Menü', 'zh': '斋月晚餐菜单'},
            'Кеды': {'de': 'Turnschuhe', 'zh': '运动鞋'},
            'Профиль Джоли 🧏\u200d♀️': {'de': 'Jolie-Profil 🧏\u200d♀️', 'zh': 'Jolie资料 🧏\u200d♀️'},
            'Рисовая карта': {'de': 'Reiskarte', 'zh': '米饭菜单'},
            'Mers': {'de': 'Mers', 'zh': 'Mers'},  # Assuming it's a proper noun without direct translation
            'Алкогольные напитки': {'de': 'Alkoholische Getränke', 'zh': '酒精饮料'},
            'Запеченные роллы': {'de': 'Gebackene Rollen', 'zh': '烤卷'},
            'Рамён': {'de': 'Ramen', 'zh': '拉面'},
            'RA1N': {'de': 'RA1N', 'zh': 'RA1N'},  # Assuming it's a proper noun without direct translation
            'Королевский': {'de': 'Königlich', 'zh': '皇家'},
            'Макаронные изделия': {'de': 'Nudelprodukte', 'zh': '面制品'},
            'Президентский': {'de': 'Präsidentiell', 'zh': '总统'},
            'Напиток виноградный крепкий': {'de': 'Starker Traubendrink', 'zh': '浓郁的葡萄饮料'},
            'Пиво': {'de': 'Bier', 'zh': '啤酒'},
            'Мешки': {'de': 'Taschen', 'zh': '袋子'},
            'Блюда на гриле': {'de': 'Gerichte vom Grill', 'zh': '烤菜品'},
            'Развивающая': {'de': 'Entwicklungs-', 'zh': '发展'},
            'Винный напиток': {'de': 'Weingetränk', 'zh': '葡萄酒饮品'},
            'Дутики': {'de': 'Stiefeletten', 'zh': '短靴'},
            'Гелиевые шарики': {'de': 'Luftballons mit Helium', 'zh': '氦气气球'},
            'Цветы в горшках': {'de': 'Blumen in Töpfen', 'zh': '盆栽花卉'},
            'Стейки/Steaks ЦЕНА ЗА 100 гр.': {'de': 'Steaks Preis pro 100 g', 'zh': '牛排价格每100克'},
            'Wines from France': {'de': 'Weine aus Frankreich', 'zh': '法国葡萄酒'},
            'HAPPY HOUR COCKTAILS 🍹': {'de': 'HAPPY HOUR COCKTAILS 🍹', 'zh': '欢乐时光鸡尾酒 🍹'},
            'HAPPY HOUR BEER 🍻': {'de': 'HAPPY HOUR BIER 🍻', 'zh': '欢乐时光啤酒 🍻'},
            'GIN 🍸': {'de': 'GIN 🍸', 'zh': 'GIN 🍸'},
            'Экстра добавки': {'de': 'Zusatzstoffe', 'zh': '额外添加剂'},
            'Хэтчбэк': {'de': 'Kombi', 'zh': '掀背车'},
            'Биг роллы': {'de': 'Big Rolls', 'zh': '大卷'},
            'Птица и кролик': {'de': 'Geflügel und Kaninchen', 'zh': '禽肉和兔肉'},
            'Ким-паб': {'de': 'Kim-Pub', 'zh': '金酒馆'},
            'Вегетарианские блюда': {'de': 'Vegetarische Gerichte', 'zh': '素食菜品'},
            'Панама': {'de': 'Panama', 'zh': '巴拿马帽'},
            'Китайская кухня/Рыба': {'de': 'Chinesische Küche/Fisch', 'zh': '中餐厅/鱼'},
            'Продукты из курицы': {'de': 'Hühnerprodukte', 'zh': '鸡制品'},
            'Пинетки': {'de': 'Babysocken', 'zh': '婴儿袜'},
            'Онлайн тренажор': {'de': 'Online-Trainingsgerät', 'zh': '在线健身器材'},
            'Паста': {'de': 'Nudeln', 'zh': '意大利面'},
            'Пижама': {'de': 'Pyjama', 'zh': '睡衣'},
            'Дерматокосметика': {'de': 'Dermatokosmetik', 'zh': '皮肤护理化妆品'},
            'Другие подарки': {'de': 'Andere Geschenke', 'zh': '其他礼品'},
            'Резиновые сапоги': {'de': 'Gummistiefel', 'zh': '橡胶靴'},
            'HAPPY HOUR WINE 🍷': {'de': 'HAPPY HOUR WEIN 🍷', 'zh': '欢乐时光葡萄酒 🍷'},
            'Горчие блюда': {'de': 'Scharfe Gerichte', 'zh': '辣菜品'},
            'Customized Cakes by Saya': {'de': 'Maßgeschneiderte Kuchen von Saya', 'zh': 'Saya定制蛋糕'},
            'Свитер': {'de': 'Pullover', 'zh': '毛衣'},
            'Мини роллы': {'de': 'Mini Rolls', 'zh': '迷你卷'},
            'Казахская кухня': {'de': 'Kasachische Küche', 'zh': '哈萨克菜'},
            'Тренажор': {'de': 'Trainingsgerät', 'zh': '健身器材'},
            'Цветы 💐': {'de': 'Blumen 💐', 'zh': '花朵 💐'},
            'Комплекты шаров': {'de': 'Ballonsets', 'zh': '气球套装'},
            'Одежда для спорта': {'de': 'Sportbekleidung', 'zh': '运动服装'},
            'Бизнес-ланчи ПЯТНИЦА': {'de': 'Business-Lunch am Freitag', 'zh': '周五商务午餐'},
            'Ресторан "Sal"': {'de': 'Restaurant "Sal"', 'zh': '“Sal”餐厅'},
            'Донер': {'de': 'Döner', 'zh': '土耳其烤肉卷'},
            'Средства защиты': {'de': 'Schutzausrüstung', 'zh': '防护装备'},
            'Crunchy & Healthy Salads': {'de': 'Knackige & Gesunde Salate', 'zh': '酥脆健康沙拉'},
            'WHITE WINE 🍷': {'de': 'WEISSWEIN 🍷', 'zh': '白葡萄酒 🍷'},
            'Говядина и баранины': {'de': 'Rind- und Lammfleisch', 'zh': '牛肉和羊肉'},
            'Такси': {'de': 'Taxi', 'zh': '出租车'},
            'Недвижимость': {'de': 'Immobilien', 'zh': '房地产'},
            'Банкетные блюда': {'de': 'Bankettgerichte', 'zh': '宴会菜品'},
            'Мясные блюда': {'de': 'Fleischgerichte', 'zh': '肉菜品'},
            'Липолитики': {'de': 'Lipolytika', 'zh': '脂肪分解药物'},
            'Блюда на мангале': {'de': 'Gerichte vom Grillspieß', 'zh': '烤肉串菜品'},
            'Гарнир': {'de': 'Beilage', 'zh': '配菜'},
            'Салаты на масле': {'de': 'Salate in Öl', 'zh': '油醋沙拉'},
            'Китайская кухня/Говядина': {'de': 'Chinesische Küche/Rindfleisch', 'zh': '中餐厅/牛肉'},
            'Наставничество': {'de': 'Mentorship', 'zh': '导师指导'},
            'Зелень': {'de': 'Grünzeug', 'zh': '绿色蔬菜'},
            'Гриль': {'de': 'Grill', 'zh': '烤架'},
            'Номер с балконом': {'de': 'Zimmer mit Balkon', 'zh': '带阳台的房间'},
            'Подушка': {'de': 'Kissen', 'zh': '枕头'},
            'Слипоны': {'de': 'Slip-Ons', 'zh': '便鞋'},
            'Курица и рыба': {'de': 'Hühnchen und Fisch', 'zh': '鸡肉和鱼肉'},
            'Стандартный': {'de': 'Standard', 'zh': '标准'},
            'Кэроб': {'de': 'Kärob', 'zh': '卡罗布'},
            'Блюда на заказ ( готовится на костре)': {'de': 'Spezialgerichte (am Lagerfeuer zubereitet)',
                                                      'zh': '订制菜品（在篝火上制作）'},
            'Горячие блюда': {'de': 'Heiße Gerichte', 'zh': '热菜'},
            'Свинина': {'de': 'Schweinefleisch', 'zh': '猪肉'},
            'Плов и добавки к плову': {'de': 'Pilaw und Beilagen', 'zh': '披萨及配菜'},
            'Образование для детей': {'de': 'Bildung für Kinder', 'zh': '儿童教育'},
            'Классические': {'de': 'Klassisch', 'zh': '经典'},
            'Добавки к плову': {'de': 'Beilagen für Pilaw', 'zh': '披萨配菜'},
            'Сувениры': {'de': 'Souvenirs', 'zh': '纪念品'},
            'Кебабы и шашлыки': {'de': 'Kebabs und Schaschliks', 'zh': '烤肉和串烧'},
            'Караоке': {'de': 'Karaoke', 'zh': '卡拉OK'},
            'Первые блюда': {'de': 'Vorspeisen', 'zh': '头盘'},
            'Лапша / Паста': {'de': 'Nudeln / Pasta', 'zh': '面条/意大利面'},
            'Арабская пицца': {'de': 'Arabische Pizza', 'zh': '阿拉伯比萨'},
            'Электромобили': {'de': 'Elektroautos', 'zh': '电动汽车'},
            'Ручка': {'de': 'Stift', 'zh': '笔'},
            'Моя категория': {'de': 'Meine Kategorie', 'zh': '我的分类'},
            'Семейный': {'de': 'Familiär', 'zh': '家庭'},
            'Виски односолодовый': {'de': 'Single Malt Whisky', 'zh': '单一麦芽威士忌'},
            'Мороженое Бингсу': {'de': 'Bingsu Eis', 'zh': '刨冰冰淇淋'},
            'Мясные полуфабрикаты': {'de': 'Fleischhalbfabrikate', 'zh': '肉类半成品'},
            'Рашгард': {'de': 'Rashguard', 'zh': '紧身衣'},
            'Блюда из морепродуктов': {'de': 'Meeresfrüchtegerichte', 'zh': '海鲜菜品'},
            'Китайская кухня/Гарниры': {'de': 'Chinesische Küche/Beilagen', 'zh': '中餐/配菜'},
            'Шаурма': {'de': 'Schawarma', 'zh': '沙尔玛'},
            'Ночники': {'de': 'Nachttöpfe', 'zh': '夜灯'},
            'Пожилой': {'de': 'Ältere', 'zh': '老年'},
            'Европейская кухня. Салаты': {'de': 'Europäische Küche. Salate', 'zh': '欧洲菜. 沙拉'},
            'Домены, веб-сайты': {'de': 'Domains, Websites', 'zh': '域名，网站'},
            'Блюда из птицы': {'de': 'Geflügelgerichte', 'zh': '家禽菜品'},
            'Шашлык на мангале': {'de': 'Schaschlik vom Grill', 'zh': '烤肉串'},
            'Боулы': {'de': 'Bowls', 'zh': '碗'},
            'Холодные Напитки': {'de': 'Kalte Getränke', 'zh': '冷饮'},
            'Туфли Дерби': {'de': 'Derby-Schuhe', 'zh': '德比鞋'},
            'Вечернее меню (после 18.00)': {'de': 'Abendmenü (nach 18:00 Uhr)', 'zh': '晚餐菜单（18:00后）'},
            'Тантуни': {'de': 'Tantuni', 'zh': '坦图尼'},
            'Улучшенный люкс': {'de': 'Verbesserter Luxus', 'zh': '豪华改良'},
            'Коммерция': {'de': 'Handel', 'zh': '商业'},
            'Дополнения к блюдам': {'de': 'Zutaten zu Gerichten', 'zh': '菜品配料'},
            'русская кухня': {'de': 'Russische Küche', 'zh': '俄罗斯菜'},
            'Маски': {'de': 'Masken', 'zh': '口罩'},
            'Ткани': {'de': 'Stoffe', 'zh': '织物'},
            'Kids меню': {'de': 'Kinder-Menü', 'zh': '儿童菜单'},
            'Пельмени': {'de': 'Pelmeni', 'zh': '饺子'},
            'Комбо наборы': {'de': 'Kombi-Sets', 'zh': '套餐'},
            'Аромадиффузоры с бамбуковыми палочками': {'de': 'Aroma-Diffusoren mit Bambusstäbchen', 'zh': '香薰扩香器与竹棒'},
            "Sundae's": {'de': 'Sundae', 'zh': '圣代'},
            'Мороженное': {'de': 'Eiscreme', 'zh': '冰淇淋'},
            'WATER 🧊': {'de': 'WASSER 🧊', 'zh': '水 🧊'},
            'Соусы для риса': {'de': 'Reissaucen', 'zh': '米饭酱料'},
            'Бабушкина стряпня': {'de': 'Omas Küche', 'zh': '奶奶的厨房'},
            'Брускетта': {'de': 'Bruschetta', 'zh': '意大利烤面包片'},
            'Постельное бельё': {'de': 'Bettwäsche', 'zh': '床上用品'},
            'Горячие блюда на пару': {'de': 'Dampfgarerichte', 'zh': '蒸菜'},
            'OZON1': {'de': 'OZON1', 'zh': 'OZON1'},
            'Фирменные блюда из курицы': {'de': 'Markengerichte mit Huhn', 'zh': '品牌鸡肉菜品'},
            'Вторые блюда': {'de': 'Hauptgerichte', 'zh': '主菜'},
            'Open air': {'de': 'Open-Air', 'zh': '露天'},
            'Бизнес-ланчи ПОНЕДЕЛЬНИК': {'de': 'Business-Lunch am Montag', 'zh': '星期一商务午餐'},
            'Крем супы': {'de': 'Cremesuppen', 'zh': '奶油汤'},
            'Для гардероба и постельного белья': {'de': 'Für Garderobe und Bettwäsche', 'zh': '衣物和床上用品'},
            'Джин': {'de': 'Gin', 'zh': '杜松子酒'},
            'Американский большой завтрак': {'de': 'Amerikanisches Frühstück', 'zh': '美式早餐'},
            'Хан Самса': {'de': 'Han Samsa', 'zh': '汉三饺'},
            'Горячие блюда / Entree': {'de': 'Heiße Gerichte / Vorspeise', 'zh': '热菜/头盘'},
            'Вареники': {'de': 'Wareniki', 'zh': '水饺'},
            'ROSÉ WINE 🍷': {'de': 'ROSÉ WEIN 🍷', 'zh': '玫瑰红酒 🍷'},
            'Горячие салаты': {'de': 'Warme Salate', 'zh': '热沙拉'},
            'Босоножки': {'de': 'Sandalen', 'zh': '凉鞋'},
            'Для уютного дома': {'de': 'Für ein gemütliches Zuhause', 'zh': '为舒适的家而设计'},
            'STARTERS & SALADS 🥗': {'de': 'Vorspeisen & Salate 🥗', 'zh': '开胃菜和沙拉 🥗'},
            'Машинки': {'de': 'Spielzeugautos', 'zh': '小汽车'},
            'Блюда с овощами': {'de': 'Gemüsegerichte', 'zh': '素菜'},
            'Ретро автомобили': {'de': 'Retro-Autos', 'zh': '复古汽车'},
            'Холодные напитки': {'de': 'Kalte Getränke', 'zh': '冷饮'},
            'Шашлыки и колбаски': {'de': 'Schaschliks und Würstchen', 'zh': '烤肉串和香肠'},
            'Такси и доставка еды': {'de': 'Taxi und Essenslieferung', 'zh': '出租车和食品送货'},
            'Семейная студия': {'de': 'Familienstudio', 'zh': '家庭工作室'},
            'Женская одежда': {'de': 'Damenbekleidung', 'zh': '女装'},
            'VR/AR': {'de': 'VR/AR', 'zh': '虚拟/增强现实'},
            'Светотехника': {'de': 'Beleuchtungstechnik', 'zh': '照明设备'},
            'Кофе с молоком': {'de': 'Milchkaffee', 'zh': '拿铁咖啡'},
            'Диетические блюда': {'de': 'Diätgerichte', 'zh': '健康餐'},
            'Хе': {'de': 'He', 'zh': '呵'},
            'Основная кухня': {'de': 'Hauptgerichte', 'zh': '主菜'},
            'Осень Зима': {'de': 'Herbst Winter', 'zh': '秋冬'},
            'Майки': {'de': 'Tanktops', 'zh': '背心'},
            'Кофе в упаковках': {'de': 'Verpackter Kaffee', 'zh': '包装咖啡'},
            'Наши Врачи': {'de': 'Unsere Ärzte', 'zh': '我们的医生'},
            'Мастермайнд': {'de': 'Meisterverstand', 'zh': '大师头脑'},
            'Зима❄️': {'de': 'Winter❄️', 'zh': '冬天❄️'},
            'Сковороды': {'de': 'Bratpfannen', 'zh': '煎锅'},
            'Жаровни': {'de': 'Bratöfen', 'zh': '烤箱'},
            'Пицца и фокачча': {'de': 'Pizza und Focaccia', 'zh': '比萨和佛卡夏'},
            'Бизнес': {'de': 'Geschäft', 'zh': '商务'},
            'Домашняя выпечка': {'de': 'Hausgemachtes Gebäck', 'zh': '家常烘焙'},
            'Китайская кухня/Салаты': {'de': 'Chinesische Küche/Salate', 'zh': '中国菜/沙拉'},
            'Каши и блины': {'de': 'Brei und Pfannkuchen', 'zh': '粥和薄饼'},
            'Китайская кухня/Супы': {'de': 'Chinesische Küche/Suppen', 'zh': '中国菜/汤'},
            'Hdhdhdh': {'de': 'Hdhdhdh', 'zh': 'Hdhdhdh'},
            'Услуги сиделок': {'de': 'Pflegedienstleistungen', 'zh': '看护服务'},
            'Пицца и бургеры': {'de': 'Pizza und Burger', 'zh': '比萨和汉堡'},
            'Статусы великих людей': {'de': 'Status großer Menschen', 'zh': '伟人的状态'},
            "Saya's Signature Drinks": {'de': 'Saya\'s Signature Drinks', 'zh': 'Saya的招牌饮品'},
            '1WOOD': {'de': '1WOOD', 'zh': '1木'},
            'Завтраки/breakfasts': {'de': 'Frühstücke', 'zh': '早餐'},
            'Птица': {'de': 'Vogel', 'zh': '禽类'},
            'Симулятор': {'de': 'Simulator', 'zh': '模拟器'},
            'Стрижки и прически': {'de': 'Haarschnitte und Frisuren', 'zh': '发型和发型设计'},
            'Супы': {'de': 'Suppen', 'zh': '汤'},
            'Корейская кухня. Салаты хе': {'de': 'Koreanische Küche. Salate he', 'zh': '韩国菜。沙拉'},
            'Детское меню': {'de': 'Kinderkarte', 'zh': '儿童菜单'},
            'Бурбон': {'de': 'Bourbon', 'zh': '波旁威士忌'},
            'Минеральная вода': {'de': 'Mineralwasser', 'zh': '矿泉水'},
            'Кыргыз чебери': {'de': 'Kirgisisches Brot', 'zh': '吉尔吉斯面包'},
            'Хиты продаж от Тесто Место': {'de': 'Bestseller von Tasto Mesto', 'zh': 'Tasto Mesto的畅销商品'},
            'Насос пениса': {'de': 'Penispumpe', 'zh': '阴茎泵'},
            'такси': {'de': 'Taxi', 'zh': '出租车'},
            'Баскет': {'de': 'Basketball', 'zh': '篮球'},
            'Ассорти из ролл': {'de': 'Rollensortiment', 'zh': '寿司拼盘'},
            'Сумка': {'de': 'Tasche', 'zh': '包'},
            'Продукты в лаваше': {'de': 'Lebensmittel in Lavash', 'zh': '薄饼食品'},
            'Конфетти': {'de': 'Konfetti', 'zh': '彩纸'},
            'Мячь': {'de': 'Ball', 'zh': '球'},
            'Бизнес ланч (с 13:00 до 16:00)': {'de': 'Business-Lunch (13:00 - 16:00 Uhr)', 'zh': '商务午餐（13:00 - 16:00）'},
            'Мужская обувь': {'de': 'Herrenschuhe', 'zh': '男鞋'},
            'Швабры и скребки для окон': {'de': 'Mopps und Fensterkratzer', 'zh': '拖把和窗刮器'},
            'Панини с картофелем фри': {'de': 'Panini mit Pommes', 'zh': '带薯条的烤面包'},
            'Топсайдеры': {'de': 'Topsider-Schuhe', 'zh': '甲板鞋'},
            'Презентация и бесплатное обучение': {'de': 'Präsentation und kostenlose Schulung', 'zh': '演示和免费培训'},
            'Салаты': {'de': 'Salate', 'zh': '沙拉'},
            'Кофты': {'de': 'Strickjacken', 'zh': '毛衣'},
            'Бульоны': {'de': 'Brühen', 'zh': '清汤'},
            'SANDWICHES 🥪': {'de': 'SANDWICHES 🥪', 'zh': '三明治🥪'},
            'Профессиональные ножи': {'de': 'Professionelle Messer', 'zh': '专业刀具'},
            'Корейская кухня': {'de': 'Koreanische Küche', 'zh': '韩国菜'},
            'Сыры': {'de': 'Käse', 'zh': '奶酪'},
            'Торты с фотопечатью': {'de': 'Kuchen mit Fotodruck', 'zh': '带照片印刷的蛋糕'},
            'Жареные Роллы': {'de': 'Gebratene Rollen', 'zh': '炸卷'},
            'Витамины': {'de': 'Vitamine', 'zh': '维生素'},
            'Лицензии, франшизы': {'de': 'Lizenzen, Franchise', 'zh': '许可证，特许经营权'},
            'Улучшенный стандарт': {'de': 'Verbesserter Standard', 'zh': '提升标准'},
            'Пасты': {'de': 'Nudeln', 'zh': '面食'},
            'Chastity lock': {'de': 'Keuschheitsschloss', 'zh': '贞操锁'},
            'Jin🍸': {'de': 'Jin🍸', 'zh': 'Jin🍸'},
            'Восточные супы': {'de': 'Ostsuppen', 'zh': '东方汤'},
            'Фаллоимитатор': {'de': 'Phalloimitator', 'zh': '仿真阳具'},
            'Добавки': {'de': 'Zusatzstoffe', 'zh': '添加剂'},
            'Корейская кухня. Первые блюда': {'de': 'Koreanische Küche. Vorspeisen', 'zh': '韩国菜。头盘'},
            'Кухонная утварь': {'de': 'Küchenutensilien', 'zh': '厨房用具'},
            'Корсеты': {'de': 'Korsetts', 'zh': '紧身胸衣'},
            'Текила': {'de': 'Tequila', 'zh': '龙舌兰酒'},
            'Лазанья': {'de': 'Lasagne', 'zh': '千层面'},
            'Гавайская кухня': {'de': 'Hawaiianische Küche', 'zh': '夏威夷菜'},
            'Информация и досуг': {'de': 'Information und Freizeit', 'zh': '信息和娱乐'},
            'Химическая настройка': {'de': 'Chemische Einstellung', 'zh': '化学调整'},
            'oZONE1': {'de': 'oZONE1', 'zh': 'oZONE1'},
            'Бургеры, брускетты, сэндвичи, панини': {'de': 'Burger, Bruschetta, Sandwiches, Panini',
                                                     'zh': '汉堡，意式烤面包，三明治，意式小面包'},
            'Китайская кухня/Курица': {'de': 'Chinesische Küche/Huhn', 'zh': '中国菜/鸡肉'},
            '🥰': {'de': '🥰', 'zh': '🥰'},
            'Супара талкан': {'de': 'Supara Talkan', 'zh': '苏帕拉塔尔坎'},
            'Алакарт': {'de': 'À la carte', 'zh': '单点菜单'},
            'Шейки из мороженого': {'de': 'Eis-Shakes', 'zh': '冰淇淋奶昔'},
            'Клаб Сэндвич': {'de': 'Club-Sandwich', 'zh': '俱乐部三明治'},
            'Товары для уборки': {'de': 'Reinigungsprodukte', 'zh': '清洁用品'},
            'Гриль и полуфабрикаты': {'de': 'Grill und Halbfertigprodukte', 'zh': '烤肉和半成品'},
            'Дублёнки': {'de': 'Lammfellmäntel', 'zh': '羊毛大衣'},
            'RUM 🥃': {'de': 'Rum', 'zh': '朗姆酒 🥃'},
            'Колбаски на мангале': {'de': 'Grillwürstchen', 'zh': '烤香肠'},
            'Бизнес-ланчи в будние дни до 16:00': {'de': 'Business-Lunch an Wochentagen bis 16:00 Uhr',
                                                   'zh': '工作日午餐截止时间16:00'},
            'В': {'de': 'In', 'zh': '在'},
            'Пылесос': {'de': 'Staubsauger', 'zh': '吸尘器'},
            'Соусы/Закуски': {'de': 'Soßen/Vorspeisen', 'zh': '酱料/开胃菜'},
            'IRISH 🥃': {'de': 'IRISCHER WHISKEY 🥃', 'zh': '爱尔兰威士忌 🥃'},
            'Горячие и запечённые роллы': {'de': 'Heiße und gebackene Rollen', 'zh': '热卷和烤卷'},
            'Кепка': {'de': 'Kappe', 'zh': '帽子'},
            'DESSERTS 🍰': {'de': 'Nachtisch 🍰', 'zh': '甜点 🍰'},
            'Корейская кухня. Вторые блюда': {'de': 'Koreanische Küche. Hauptgerichte', 'zh': '韩国菜。主菜'},
            'LeaderCombo': {'de': 'Führerkombo', 'zh': '领导者组合'},
            'Бургеры фирменные': {'de': 'Marken-Burger', 'zh': '品牌汉堡'},
            'Категория': {'de': 'Kategorie', 'zh': '类别'},
            'Энергетические напитки': {'de': 'Energiegetränke', 'zh': '能量饮料'},
            'Специальное предложение': {'de': 'Sonderangebot', 'zh': '特价'},
            'Европейская кухня. Первые блюда': {'de': 'Europäische Küche. Vorspeisen', 'zh': '欧洲菜。头盘'},
            'Бургеры': {'de': 'Burger', 'zh': '汉堡'},
            'Картины': {'de': 'Gemälde', 'zh': '画'},
            'Суши': {'de': 'Sushi', 'zh': '寿司'},
            'Вторые блюда-Китайская кухня': {'de': 'Hauptgerichte-Chinesische Küche', 'zh': '主菜-中国菜'},
            'Шампанское': {'de': 'Champagner', 'zh': '香槟'},
            'Дом': {'de': 'Zuhause', 'zh': '家'},
            'Салфетки и варежки для лица': {'de': 'Servietten und Gesichtshandschuhe', 'zh': '餐巾纸和面巾'},
            'Манты': {'de': 'Manti', 'zh': '蒙古包'},
            'AMERICAN 🥃': {'de': 'AMERIKANISCHER WHISKEY 🥃', 'zh': '美国威士忌 🥃'},
            'TV': {'de': 'Fernsehen', 'zh': '电视'},
            'Блюда из свинины': {'de': 'Schweinefleischgerichte', 'zh': '猪肉菜'},
            'Блюда для компании': {'de': 'Gerichte für Unternehmen', 'zh': '公司菜'},
            'Мясная карта': {'de': 'Fleischkarte', 'zh': '肉类菜单'},
            'Варежки для тела': {'de': 'Körperhandschuhe', 'zh': '身体手套'},
            'Завтрак': {'de': 'Frühstück', 'zh': '早餐'},
            'Китайская кухня/Блюда на жаровне': {'de': 'Chinesische Küche/Gerichte auf dem Grill', 'zh': '中国菜/烧烤菜'},
            'Стрижка волос': {'de': 'Haarschnitt', 'zh': '理发'},
            'Фены': {'de': 'Haartrockner', 'zh': '吹风机'},
            'Вентиляторы': {'de': 'Ventilatoren', 'zh': '风扇'},
            'Тарифы 💲': {'de': 'Tarife 💲', 'zh': '费率 💲'},
            'Блюда на мангале/BBQ': {'de': 'Grillgerichte/BBQ', 'zh': '烤肉/烧烤'},
            'Полусапожки': {'de': 'Halbstiefel', 'zh': '短靴'},
            'Французская кухня': {'de': 'Französische Küche', 'zh': '法国菜'},
            'Салаты ': {'de': 'Salate', 'zh': '沙拉'},
            'Beer 🍺': {'de': 'Bier 🍺', 'zh': '啤酒 🍺'},
            'Плакетки': {'de': 'Plaketten', 'zh': '纪念牌'},
            'Файры': {'de': 'Feuerwerke', 'zh': '烟火'},
            'Баскетбол': {'de': 'Basketball', 'zh': '篮球'},
            'Коттедж': {'de': 'Landhaus', 'zh': '别墅'},
            'Авто': {'de': 'Auto', 'zh': '汽车'},
            "Nature's Own Factory": {'de': 'Naturfabrik', 'zh': '大自然的工厂'},
            'Салат': {'de': 'Salat', 'zh': '沙拉'},
            'Фирменные стейки': {'de': 'Markensteaks', 'zh': '品牌牛排'},
            'Суши / Sushi': {'de': 'Sushi', 'zh': '寿司'},
            'Фото': {'de': 'Foto', 'zh': '照片'},
            'Блюда из телятины': {'de': 'Kalbfleischgerichte', 'zh': '小牛肉菜'},
            'Сэндвичи на тосте с картофелем фри': {'de': 'Sandwiches auf Toast mit Pommes', 'zh': '烤面包三明治配薯条'},
            'Школьная форма': {'de': 'Schuluniform', 'zh': '校服'},
            'Психология': {'de': 'Psychologie', 'zh': '心理学'},
            'Monster Dildo': {'de': 'Monster-Dildo', 'zh': '怪物假阳具'},
            'Овощные блюда1': {'de': 'Gemüsegerichte 1', 'zh': '蔬菜菜品1'},
            'Автомобили эконом': {'de': 'Wirtschaftsautos', 'zh': '经济型汽车'},
            'Воркшоп': {'de': 'Workshop', 'zh': '研讨会'},
            'Мясо на гриле': {'de': 'Grillfleisch', 'zh': '烧烤肉'},
            'Woke': {'de': 'Aufgewacht', 'zh': '觉醒'},
            'Маски для волос и масла': {'de': 'Haarmasken und Öle', 'zh': '头发面膜和油'},
            'Sexy': {'de': 'Sexy', 'zh': '性感'},
            'Пицца на тонком тесте': {'de': 'Dünner Teigpizza', 'zh': '薄饼披萨'},
            'Салфетки против сильных загрязнений': {'de': 'Tücher gegen starke Verschmutzung', 'zh': '抗强污染抹布'},
            'Кросовки': {'de': 'Turnschuhe', 'zh': '运动鞋'},
            'Блокаторы вируса': {'de': 'Virusblocker', 'zh': '病毒阻滞剂'},
            'JUICES 🧃': {'de': 'Säfte 🧃', 'zh': '果汁 🧃'},
            'Блюда на компанию': {'de': 'Gerichte für Unternehmen', 'zh': '公司菜'},
            'Здоровое меню': {'de': 'Gesunde Speisekarte', 'zh': '健康菜单'},
            'Стейк': {'de': 'Steak', 'zh': '牛排'},
            'VEGAN 🥦': {'de': 'Vegan 🥦', 'zh': '纯素 🥦'},
            'Монгольский гриль': {'de': 'Mongolisches Grillen', 'zh': '蒙古烧烤'},
            'Пробки': {'de': 'Stöpsel', 'zh': '塞子'},
            'Гели для мытья посуды': {'de': 'Spülmittel', 'zh': '洗碗液'},
            'Велосипедки': {'de': 'Fahrradhosen', 'zh': '自行车裤'},
            'ДЕМИ': {'de': 'DEMI', 'zh': 'DEMI'},
            'Салфетки для стекла': {'de': 'Glasreinigungstücher', 'zh': '玻璃清洁纸巾'},
            'Наша команда': {'de': 'Unser Team', 'zh': '我们的团队'},
            'Индийский Чаат': {'de': 'Indischer Chaat', 'zh': '印度小吃'},
            'Цветы по штучно': {'de': 'Blumen einzeln', 'zh': '逐朵花'},
            'Кебаб': {'de': 'Kebab', 'zh': '烤肉串'},
            'Презентация': {'de': 'Präsentation', 'zh': '展示'},
            'Мужская одежда': {'de': 'Herrenbekleidung', 'zh': '男装'},
            'Заготовки': {'de': 'Vorbereitungen', 'zh': '备料'},
            'Восточные салаты': {'de': 'Ostsalate', 'zh': '东方沙拉'},
            'Ресницы': {'de': 'Wimpern', 'zh': '睫毛'},
            'Холодные и горячие закуски': {'de': 'Kalte und warme Snacks', 'zh': '冷热小吃'},
            'Салаты и закуски': {'de': 'Salate und Snacks', 'zh': '沙拉和小吃'},
            'Поке': {'de': 'Poke', 'zh': '捞饭'},
            'Информация и стратегия': {'de': 'Information und Strategie', 'zh': '信息和策略'},
            'Кухонные принадлежности': {'de': 'Küchenutensilien', 'zh': '厨房用具'},
            'Завтраки': {'de': 'Frühstück', 'zh': '早餐'},
            'Чай': {'de': 'Tee', 'zh': '茶'},
            'Куриная продукция (цена указана за 1 кг.)': {'de': 'Hühnerprodukte (Preis pro kg)', 'zh': '鸡肉产品（每公斤价格）'},
            'Сыжаклар': {'de': 'Käseprodukte', 'zh': '奶酪制品'},
            'По-домашнему': {'de': 'Hausgemacht', 'zh': '家常'},
            'Мясо': {'de': 'Fleisch', 'zh': '肉'},
            'Домашние колбаски': {'de': 'Hausgemachte Würstchen', 'zh': '家制香肠'},
            'Кюлоты': {'de': 'Culottes', 'zh': '裤裙'},
            'Кексы': {'de': 'Muffins', 'zh': '松饼'},
            'VIP автомобили': {'de': 'VIP-Autos', 'zh': '豪华汽车'},
            'Кыргызская кухня': {'de': 'Kirgisische Küche', 'zh': '吉尔吉斯菜'},
            'Насосы': {'de': 'Pumpen', 'zh': '泵'},
            'VR обучение': {'de': 'VR-Training', 'zh': '虚拟现实培训'},
            'Шашлыки и стейки': {'de': 'Schaschlik und Steaks', 'zh': '烤肉串和牛排'},
            'Рамен': {'de': 'Ramen', 'zh': '拉面'},
            'Халаты': {'de': 'Bademäntel', 'zh': '浴袍'},
            'Хлеб': {'de': 'Brot', 'zh': '面包'},
            'Торты на заказ': {'de': 'Kuchen auf Bestellung', 'zh': '定制蛋糕'},
            'Горячие закуски и выпечка': {'de': 'Warme Snacks und Gebäck', 'zh': '热小吃和糕点'},
            'Ботокс до и после ✨': {'de': 'Botox vorher und nachher ✨', 'zh': '玻尿酸前后 ✨'},
            'Кофе с алкоголем': {'de': 'Kaffee mit Alkohol', 'zh': '酒咖啡'},
            'Узбекская кухня': {'de': 'Usbekische Küche', 'zh': '乌兹别克菜'},
            'Гёзлеме': {'de': 'Gözleme', 'zh': '格兹勒姆'},
            'Коктейли': {'de': 'Cocktails', 'zh': '鸡尾酒'},
            'Национальные блюда': {'de': 'Nationale Gerichte', 'zh': '民族菜'},
            'Холодильник': {'de': 'Kühlschrank', 'zh': '冰箱'},
            'Подтяжка бровей нитями 🦊': {'de': 'Augenbrauenlifting mit Fäden 🦊', 'zh': '线雕提眉 🦊'},
            'Насадки': {'de': 'Aufsätze', 'zh': '附件'},
            'Для молодоженов': {'de': 'Für Brautpaare', 'zh': '新人'},
            'Австрийская кухня': {'de': 'Österreichische Küche', 'zh': '奥地利菜'},
            'Престижные автомобили': {'de': 'Prestigeautos', 'zh': '豪车'},
            'Унты': {'de': 'Stiefel', 'zh': '靴子'},
            'Полуфабрикаты': {'de': 'Halbfertigprodukte', 'zh': '半成品'},
            'Вертолёты': {'de': 'Hubschrauber', 'zh': '直升机'},
            'Гарниры/Мучное': {'de': 'Beilagen/Teigwaren', 'zh': '配菜/面食'},
            'Корейская кухня. Салаты': {'de': 'Koreanische Küche. Salate', 'zh': '韩国菜。沙拉'},
            'Мочалки': {'de': 'Schwämme', 'zh': '擦布'},
            'Холи': {'de': 'Holi', 'zh': '印度色彩节'},
            'Big grill': {'de': 'Großer Grill', 'zh': '大烧烤'},
            'Масло': {'de': 'Öl', 'zh': '油'},
            'Ботинки': {'de': 'Stiefel', 'zh': '靴子'},
            'Губки до и после 👄': {'de': 'Schwämme vorher und nachher 👄', 'zh': '擦布前后 👄'},
            'Блюда из мяса': {'de': 'Fleischgerichte', 'zh': '肉菜'},
            'Замороженная продукция': {'de': 'Tiefkühlprodukte', 'zh': '冷冻食品'},
            'Диетическое меню': {'de': 'Diätkarte', 'zh': '减肥菜单'},
            'Мангал': {'de': 'Grill', 'zh': '烤架'},
            'TEQUILA 🍸': {'de': 'TEQUILA 🍸', 'zh': '龙舌兰酒 🍸'},
            'Вебинар': {'de': 'Webinar', 'zh': '网络研讨会'},
            'Горячий шоколад': {'de': 'Heiße Schokolade', 'zh': '热巧克力'},
            'Закуски к пиву': {'de': 'Bierhäppchen', 'zh': '啤酒小吃'},
            'Аутентичные Бургеры': {'de': 'Authentische Burger', 'zh': '正宗汉堡'},
            'Чистящая паста': {'de': 'Reinigungspaste', 'zh': '清洁膏'},
            'Колбасы': {'de': 'Würste', 'zh': '香肠'},
            'Блюда на жаровне': {'de': 'Pfannengerichte', 'zh': '平底锅菜'},
            'Внедорожник': {'de': 'Geländewagen', 'zh': '越野车'},
            'Хлеб и выпечка': {'de': 'Brot und Gebäck', 'zh': '面包和糕点'},
            'Фирменные блюда': {'de': 'Markengerichte', 'zh': '品牌菜'},
            'Пивной сет': {'de': 'Bier-Set', 'zh': '啤酒套餐'},
            'Chicken&Fries': {'de': 'Hähnchen und Pommes', 'zh': '鸡肉和薯条'},
            'Люстры': {'de': 'Lüster', 'zh': '吊灯'},
            'Холодный чай': {'de': 'Eistee', 'zh': '冷茶'},
            'Вторые блюда национальной кухни': {'de': 'Zweite Gerichte der nationalen Küche', 'zh': '国菜第二道菜'},
            'Классические роллы': {'de': 'Klassische Rollen', 'zh': '经典卷'},
            'Сосиски': {'de': 'Würstchen', 'zh': '香肠'},
            'Блюда для большой компании (залог за блюдо 1000 сом )': {
                'de': 'Gerichte für große Gruppen (Pfand für Gericht 1000 Som)', 'zh': '大公司菜肴（每道菜1000索姆保证金）'},
            'завтрак': {'de': 'Frühstück', 'zh': '早餐'},
            'Совместный номер': {'de': 'Gemeinsames Zimmer', 'zh': '合住房间'},
            'Обзор JVC': {'de': 'JVC-Überblick', 'zh': 'JVC评论'},
            'Препараты Ботулотоксина 💊': {'de': 'Botulinumtoxin-Präparate 💊', 'zh': '肉毒杆菌毒素制剂 💊'},
            'Салаты хе': {'de': 'He Salate', 'zh': '和风沙拉'},
            'Сэндвич роллы': {'de': 'Sandwich-Rollen', 'zh': '三明治卷'},
            'ЗИМА ❄️🌨': {'de': 'WINTER ❄️🌨', 'zh': '冬季 ❄️🌨'},
            'Японская кухня': {'de': 'Japanische Küche', 'zh': '日本料理'},
            'Фасилитация': {'de': 'Facilitation', 'zh': '促进'},
            'Шампуни': {'de': 'Shampoos', 'zh': '洗发水'},
            'Валенки': {'de': 'Valenki (russische Filzstiefel)', 'zh': '瓦连基（俄罗斯毡靴）'},
            'Ланч': {'de': 'Mittagessen', 'zh': '午餐'},
            'Фокачча': {'de': 'Focaccia', 'zh': '佛卡夏'},
            'BREAKFAST 🍳': {'de': 'FRÜHSTÜCK 🍳', 'zh': '早餐 🍳'},
            'Блюда к красному вину': {'de': 'Gerichte zu Rotwein', 'zh': '红酒佐餐'},
            'Фирменные немецкие колбаски': {'de': 'Markendeutsche Würstchen', 'zh': '德国名牌香肠'},
            'Перманентный макияж': {'de': 'Permanent Make-up', 'zh': '永久化妆'},
            'Сникеры': {'de': 'Sneakers', 'zh': '运动鞋'},
            'Кавказская кухня': {'de': 'Kaukasische Küche', 'zh': '高加索料理'},
            'Коуч , психология': {'de': 'Coaching, Psychologie', 'zh': '教练，心理学'},
            'Переводы': {'de': 'Übersetzungen', 'zh': '翻译'}

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
