from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, filters
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException, PermissionDeniedException
from notifications.constants import NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION, \
    NOTIFICATION_TYPE_AVAILABLE_DELIVERY, NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT
from notifications.models import Notification
from organizations.serializers.card_serializers import DiscountCardBriefSerializer
from organizations.serializers.organization_serializers import (
    PartnerWithLatestTransactionSerializer, PartnerWithLatestTransactionUnprocessedTransactionCountSerializer,
)
from organizations.serializers.query_param_serializers import OrganizationTransactionsQueryParamSerializer
from organizations.services.card_services import DiscountCardService
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.organization_services import OrganizationService
from shop.services.cart_services import CartService
from shop.services.booking_services import BookingService
from shop.services.item_services import ShopItemService
from transactions.models import Transaction
from transactions.serializers.stats_serializers import TotalStatsSerializer
from transactions.serializers.transaction_serializers import (
    PreprocessSerializer, CompleteSerializer, TransactionsSerializer, StartEndDateTransactionSerializer,
    TransactionDetailSerializer, TransactionWithClientSerializer, OnlineCompleteSerializer,
    BookingTransactionWithClientSerializer, OnlinePaymentCompleteSerializer, CompleteBookingSerializer,
    OrganizationRentalTransactionWithClientSerializer
)
from shop.serializers.item_serializers import BookInfoWithClientSerializer
from shop.models import ShopItem, Booking
from transactions.services.filters import TransactionFilter
from transactions.services.transaction_services import TransactionService
from users.serializers import ProfileBriefWithPhotoSerializer, UserShortInfoSerializer


class TransactionPreprocessView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PreprocessSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        client = serializer.validated_data['client']
        cart = serializer.validated_data.get('cart', None)

        new_transaction = TransactionService.preprocess_transaction(
            client=client, organization=organization, cart=cart, processed_by=request.user
        )

        cumulative = OrganizationClientFinancialStatusService.get_client_cumulative_card(client=client,
                                                                                         organization=organization)
        fixed = DiscountCardService.get_fixed_discounts_of_organization(organization=organization)
        cashback = DiscountCardService.get_cashback_discounts_of_organization(organization=organization)

        accrued_cashback = OrganizationClientFinancialStatusService.get_client_accrued_cashback(
            client=client, organization=organization
        )

        if cumulative is not None:
            cumulative = DiscountCardBriefSerializer(cumulative).data

        discounted_price = 0 if cart is None else CartService.get_total_prices_in_cart(cart=cart)[1]

        data = {
            'transaction_id': new_transaction.id,
            'purchase_id': organization.running_purchase_id,
            'cumulative': cumulative,
            'fixed': DiscountCardBriefSerializer(fixed, many=True).data,
            'cashback': DiscountCardBriefSerializer(cashback, many=True).data,
            'accrued_cashback': accrued_cashback,
            'client': ProfileBriefWithPhotoSerializer(client, context={'request': request}).data,
            'cart_amount': discounted_price,
        }

        return Response(data=data, status=status.HTTP_200_OK)


class TransactionBookingPreprocessView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookInfoWithClientSerializer

    def post(self, request, pk):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)


        rental = ShopItem.objects.get(id=pk)
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']
        organization = serializer.validated_data['organization']
        client = serializer.validated_data['client']
        booking = Booking.objects.create(user=request.user,
                                         item=rental,
                                         organization=organization,
                                         start_time=start_time,
                                         end_time=end_time
                                         )

        new_transaction = TransactionService.preprocess_booking_transaction(
            client=client, organization=organization, booking=booking, processed_by=request.user
        )

        cumulative = OrganizationClientFinancialStatusService.get_client_cumulative_card(client=client,
                                                                                         organization=organization)
        fixed = DiscountCardService.get_fixed_discounts_of_organization(organization=organization)
        cashback = DiscountCardService.get_cashback_discounts_of_organization(organization=organization)

        accrued_cashback = OrganizationClientFinancialStatusService.get_client_accrued_cashback(
            client=client, organization=organization
        )

        if cumulative is not None:
            cumulative = DiscountCardBriefSerializer(cumulative).data

        discounted_price = 0 if booking is None else BookingService.get_total_prices_in_booking(booking=booking)[1]

        data = {
            'transaction_id': new_transaction.id,
            'purchase_id': organization.running_purchase_id,
            'cumulative': cumulative,
            'fixed': DiscountCardBriefSerializer(fixed, many=True).data,
            'cashback': DiscountCardBriefSerializer(cashback, many=True).data,
            'accrued_cashback': accrued_cashback,
            'client': ProfileBriefWithPhotoSerializer(client, context={'request': request}).data,
            'cart_amount': discounted_price,
        }

        return Response(data=data, status=status.HTTP_200_OK)


class TransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        TransactionService.complete_transaction(
            transaction_id=serializer.validated_data['transaction_id'],
            processed_by=request.user,
            original_amount=serializer.validated_data['original_amount'],
            discount_percent=serializer.validated_data['discount_percent'],
            source_card=serializer.validated_data['source_card'],
            from_cashback=serializer.validated_data['from_cashback'],
            utc_offset_minutes=serializer.validated_data.get('utc_offset_minutes'),
            cart=serializer.validated_data.get('cart', None),
        )

        return Response(data={
            'message': _('Transaction successfully completed')
        }, status=status.HTTP_200_OK)


class TransactionBookingCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompleteBookingSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        transaction = Transaction.objects.get(id=serializer.validated_data['transaction_id'])
        booking = transaction.booking

        TransactionService.complete_booking_transaction(
            transaction_id=serializer.validated_data['transaction_id'],
            processed_by=request.user,
            original_amount=serializer.validated_data['original_amount'],
            discount_percent=serializer.validated_data['discount_percent'],
            source_card=serializer.validated_data['source_card'],
            from_cashback=serializer.validated_data['from_cashback'],
            booking=booking,
        )

        return Response(data={
            'message': _('Transaction successfully completed')
        }, status=status.HTTP_200_OK)


class OnlineTransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        TransactionService.complete_online_transaction(
            transaction_id=serializer.validated_data['transaction_id'],
            utc_offset_minutes=serializer.validated_data.get('utc_offset_minutes'),
            processed_by=request.user,
            request=request
        )

        return Response(data={
            'message': _('Transaction successfully completed')
        }, status=status.HTTP_200_OK)


class OnlineBookingTransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        TransactionService.complete_booking_online_transaction(
            transaction_id=serializer.validated_data['transaction_id'],
            utc_offset_minutes=serializer.validated_data.get('utc_offset_minutes'),
            processed_by=request.user,
            request=request
        )

        return Response(data={
            'message': _('Transaction successfully completed')
        }, status=status.HTTP_200_OK)


class UserTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        return TransactionService.get_user_transaction_organizations(
            client=self.request.user,
            start_date=serializer.validated_data.get('start'),
            end_date=serializer.validated_data.get('end')
        )


class UserSaleTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionUnprocessedTransactionCountSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        return TransactionService.get_user_sale_transaction_organizations(
            user=self.request.user,
            start_date=serializer.validated_data.get('start'),
            end_date=serializer.validated_data.get('end')
        )


class UserSaleRentalTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionUnprocessedTransactionCountSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        return TransactionService.get_user_sale_rental_transaction_organizations(
            user=self.request.user,
            start_date=serializer.validated_data.get('start'),
            end_date=serializer.validated_data.get('end')
        )


class UserTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get('HTTP_CURRENCY', settings.APP_BASE_CURRENCY)

        totals = TransactionService.get_user_totals(client=request.user, currency=currency,
                                                    organization=organization,
                                                    start_date=serializer.validated_data.get('start'),
                                                    end_date=serializer.validated_data.get('end'))
        totals['total_savings'] += totals['total_from_cashback']
        data = TotalStatsSerializer(totals).data
        return Response(data)


class UserSaleTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get('HTTP_CURRENCY', settings.APP_BASE_CURRENCY)

        totals = TransactionService.get_user_sale_totals(processed_by=request.user, currency=currency,
                                                         organization=organization,
                                                         start_date=serializer.validated_data.get('start'),
                                                         end_date=serializer.validated_data.get('end'))
        totals['total_savings'] += totals['total_from_cashback']
        data = TotalStatsSerializer(totals).data
        return Response(data)

class UserSaleRentalTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get('HTTP_CURRENCY', settings.APP_BASE_CURRENCY)

        totals = TransactionService.get_user_sale_rental_totals(processed_by=request.user, currency=currency,
                                                         organization=organization,
                                                         start_date=serializer.validated_data.get('start'),
                                                         end_date=serializer.validated_data.get('end'))
        totals['total_savings'] += totals['total_from_cashback']
        data = TotalStatsSerializer(totals).data
        return Response(data)


class UserTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ['id']

    def get_queryset(self):
        transactions = TransactionService.get_user_transactions(client=self.request.user, )
        return transactions


class UserSaleTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ['id']

    def get_queryset(self):
        transactions = TransactionService.get_user_sale_transactions(user=self.request.user)
        return transactions


class UserTransactionDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        instance = TransactionService.get_transaction(transaction_id=pk, requested_by=request.user)
        return Response(TransactionDetailSerializer(instance, context={'request': request, "user": request.user}).data)


class OrganizationTransactionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    queryset = Transaction.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = OrganizationTransactionsQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        if not OrganizationService.user_can_see_stats(organization=serializer.validated_data['organization'],
                                                      user=request.user):
            raise NotAcceptableException(_('No rights to see stats of organization'))

        queryset = TransactionService.get_organization_transactions(
            organization=serializer.validated_data['organization'],
            processed_by=serializer.validated_data['processed_by'],
            start_date=serializer.validated_data['start'],
            end_date=serializer.validated_data['end'],
            search_id=serializer.validated_data['search'],
            client=serializer.validated_data['client']
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrganizationTransactionRetrieveDestroyView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithClientSerializer

    def get_object(self):
        return TransactionService.get_transaction(transaction_id=self.kwargs['pk'], requested_by=self.request.user)

    def perform_destroy(self, instance: Transaction):
        # ToDo: implement proper cancellation of transactions
        if not OrganizationService.user_can_see_stats(organization=instance.organization, user=self.request.user):
            raise PermissionDeniedException(_('Permission denied'))

        TransactionService.refund_transaction(old_transaction=instance, user=self.request.user, request=self.request)

        transaction.on_commit(
            lambda: Notification.objects.filter(
                extra_data__transaction_id=instance.id,
                type__in=[NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                          NOTIFICATION_TYPE_AVAILABLE_DELIVERY,
                          NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT]
            ).delete())


class OrganizationBookingTransactionRetrieveDestroyView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingTransactionWithClientSerializer

    def get_object(self):
        return TransactionService.get_transaction(transaction_id=self.kwargs['pk'], requested_by=self.request.user)

    def perform_destroy(self, instance: Transaction):
        # ToDo: implement proper cancellation of transactions
        if not OrganizationService.user_can_see_stats(organization=instance.organization, user=self.request.user):
            raise PermissionDeniedException(_('Permission denied'))

        TransactionService.refund_booking_transaction(old_transaction=instance, user=self.request.user, request=self.request)

        transaction.on_commit(
            lambda: Notification.objects.filter(
                extra_data__transaction_id=instance.id,
                type__in=[NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                          NOTIFICATION_TYPE_AVAILABLE_DELIVERY,
                          NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT]
            ).delete())


class OrgFollowersTransactionsListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ['id']

    def get_queryset(self):
        return TransactionService.get_organization_follower_transactions(organization_id=self.kwargs['organization_id'],
                                                                         requested_by=self.request.user,
                                                                         follower_id=self.kwargs['user_id'])


class UserUnprocessedTransactionCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = TransactionService.get_unprocessed_transactions_count(user=request.user)
        data = dict(count=count)
        return Response(data, status=status.HTTP_200_OK)


class OrganizationUsersTransactionView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserShortInfoSerializer
    search_fields = ['full_name', 'username']
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs['pk'])
        if not OrganizationService.user_can_see_stats(organization=organization,
                                                      user=self.request.user):
            raise NotAcceptableException(_('No rights to see stats of organization'))
        return TransactionService.get_users_of_transactions_in_organization(organization=organization,
                                                                            processed_by=self.request.user)


class OrganizationRentalUsersTransactionView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationRentalTransactionWithClientSerializer

    def list(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        rental = ShopItemService.get(id=self.kwargs['pk'])
        queryset = TransactionService.get_organization_processed_transactions(
            rental=rental,
            start_date=serializer.validated_data.get('start'),
            end_date=serializer.validated_data.get('end')
        )

        search = self.request.GET.get('search', None)
        if search:
            queryset = TransactionService.get_ordering_search_result(queryset=queryset, search_word=search)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class RentPaymentAcceptView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlinePaymentCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        TransactionService.accept_booking_transaction_by_user(transaction_id=serializer.validated_data['transaction_id'], user=self.request.user,
                                                              request=self.request)

        return Response(data={
            'message': _('Transaction successfully paid')
        }, status=status.HTTP_200_OK)


class RentPaymentRejectView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingTransactionWithClientSerializer

    def get_object(self):
        return TransactionService.get_transaction(transaction_id=self.kwargs['pk'], requested_by=self.request.user)

    def perform_destroy(self, instance: Transaction):
        TransactionService.reject_booking_transaction_by_user(old_transaction=instance, user=self.request.user,
                                                      request=self.request)


