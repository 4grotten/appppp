from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException, PermissionDeniedException
from organizations.serializers.card_serializers import DiscountCardBriefSerializer
from organizations.serializers.organization_serializers import PartnerWithLatestTransactionSerializer
from organizations.serializers.query_param_serializers import OrganizationTransactionsQueryParamSerializer
from organizations.services.card_services import DiscountCardService
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.organization_services import OrganizationService
from transactions.models import Transaction
from transactions.serializers.stats_serializers import TotalStatsSerializer
from transactions.serializers.transaction_serializers import (
    PreprocessSerializer, CompleteSerializer, TransactionsSerializer, StartEndDateTransactionSerializer,
    TransactionDetailSerializer, TransactionWithClientSerializer
)
from transactions.services.filters import TransactionFilter
from transactions.services.transaction_services import TransactionService
from users.serializers import ProfileBriefWithPhotoSerializer


class TransactionPreprocessView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PreprocessSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = serializer.validated_data['organization']
        client = serializer.validated_data['client']

        new_transaction = TransactionService.preprocess_transaction(
            client=client, organization=organization, processed_by=request.user
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

        data = {
            'transaction_id': new_transaction.id,
            'cumulative': cumulative,
            'fixed': DiscountCardBriefSerializer(fixed, many=True).data,
            'cashback': DiscountCardBriefSerializer(cashback, many=True).data,
            'accrued_cashback': accrued_cashback,
            'client': ProfileBriefWithPhotoSerializer(client, context={'request': request}).data
        }

        return Response(data=data, status=status.HTTP_200_OK)


class TransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        TransactionService.complete_transaction(
            transaction_id=serializer.validated_data['transaction_id'],
            processed_by=request.user,
            original_amount=serializer.validated_data['original_amount'],
            discount_percent=serializer.validated_data['discount_percent'],
            source_card=serializer.validated_data['source_card'],
            from_cashback=serializer.validated_data['from_cashback'],
        )

        return Response(data={
            'message': 'Transaction successfully completed'
        }, status=status.HTTP_200_OK)


class UserTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        return TransactionService.get_user_transaction_organizations(
            client=self.request.user,
            start_date=serializer.validated_data.get('start'),
            end_date=serializer.validated_data.get('end')
        )


class UserTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
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


class UserTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ['id']

    def get_queryset(self):
        transactions = TransactionService.get_user_transactions(client=self.request.user, )
        return transactions


class UserTransactionDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        instance = TransactionService.get_transaction(transaction_id=pk, requested_by=request.user)
        return Response(TransactionDetailSerializer(instance).data)


class OrganizationTransactionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    queryset = Transaction.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = OrganizationTransactionsQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        if not OrganizationService.user_can_see_stats(organization=serializer.validated_data['organization'],
                                                      user=request.user):
            raise NotAcceptableException('No rights to see stats of organization')

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
            raise PermissionDeniedException('Permission denied')

        TransactionService.refund_transaction(old_transaction=instance)


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
