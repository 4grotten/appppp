from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.generics import GenericAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.serializers.card_serializers import DiscountCardBriefSerializer
from organizations.serializers.organization_serializers import PartnerSerializer
from organizations.services.card_services import DiscountCardService
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from transactions.serializers.stats_serializers import TotalStatsSerializer
from transactions.serializers.transaction_serializers import (
    PreprocessSerializer, CompleteSerializer, TransactionsSerializer, StartEndDateTransactionSerializer,
    TransactionDetailSerializer
)
from transactions.services.filters import TransactionFilter
from transactions.services.transaction_services import TransactionService
from users.serializers import ProfileBriefSerializer


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

        transaction = TransactionService.preprocess_transaction(
            client=client, organization=organization, processed_by=request.user
        )

        cumulative = OrganizationClientFinancialStatusService.get_client_cumulative_card(client=client,
                                                                                         organization=organization)
        fixed = DiscountCardService.get_fixed_discounts_of_organization(organization=organization)

        if cumulative is not None:
            cumulative = DiscountCardBriefSerializer(cumulative).data

        data = {
            'transaction_id': transaction.id,
            'cumulative': cumulative,
            'fixed': DiscountCardBriefSerializer(fixed, many=True).data,
            'client': ProfileBriefSerializer(client).data
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
            source_card=serializer.validated_data['source_card']
        )

        return Response(data={
            'message': 'Transaction successfully completed'
        }, status=status.HTTP_200_OK)


class TransactionOrganizationsView(ListAPIView):
    serializer_class = PartnerSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        organizations = TransactionService.get_user_transaction_organizations(client=self.request.user,
                                                                              start_date=serializer.validated_data.get(
                                                                                  'start'),
                                                                              end_date=serializer.validated_data.get(
                                                                                  'end'))
        return organizations


class TransactionUserTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        currency = request.META.get('HTTP_CURRENCY', settings.APP_BASE_CURRENCY)
        totals = TransactionService.get_user_totals(client=request.user, currency=currency,
                                                    start_date=serializer.validated_data.get('start'),
                                                    end_date=serializer.validated_data.get('end'))
        data = TotalStatsSerializer(totals).data
        return Response(data)


class TransactionsListApiView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ['id']

    def get_queryset(self):
        transactions = TransactionService.get_user_transactions(client=self.request.user, )
        return transactions


class TransactionDetailAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionDetailSerializer

    def get(self, request, pk):
        transaction = TransactionService.get_user_transaction_detail(user=request.user, transaction_id=pk)

        return Response(self.serializer_class(transaction, many=False, context={'request': request}).data)
