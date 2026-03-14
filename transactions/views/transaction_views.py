import hashlib
import json
from decimal import ROUND_DOWN, Decimal
from time import time
from organizations.services.profitgate_service import ProfitgateService
from payments.models import ProfitgateOrganizationPaymentSystem
import requests
import xmltodict
from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    CreateAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
    RetrieveDestroyAPIView,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import (
    BadRequestException,
    NotAcceptableException,
    PermissionDeniedException,
)
from common.services.currency import CurrencyConverterService
from notifications.constants import (
    NOTIFICATION_TYPE_AVAILABLE_DELIVERY,
    NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
    NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT,
)
from notifications.models import Notification
from organizations.serializers.card_serializers import DiscountCardBriefSerializer
from organizations.serializers.organization_serializers import (
    PartnerWithLatestTransactionSerializer,
    PartnerWithLatestTransactionUnprocessedTransactionCountSerializer,
    PartnerWithTicketLatestTransactionUnprocessedTransactionCountSerializer,
    PartnerWithWithdrawalLatestTransactionUnprocessedTransactionCountSerializer,
)
from organizations.serializers.query_param_serializers import (
    OrganizationTransactionsQueryParamSerializer,
)
from organizations.services.card_services import DiscountCardService
from organizations.services.client_status_services import (
    OrganizationClientFinancialStatusService,
)
from organizations.services.maalypay_service import MaalyPayService
from organizations.services.organization_services import OrganizationService
from organizations.tasks import fetch_maalypay_status
from project.redis_client import redis_client
from project.settings.base import (
    BETAPAY_API_TOKEN,
    CRYPTOCLOUD_API_KEY,
    CRYPTOCLOUD_SHOP_ID,
    FREEDOMPAY_PROJECT_ID,
    FREEDOMPAY_RECEIVE_SECRET,
    LIBERSAVE_API_KEY,
    PAYSY_API_KEY,
)
from shop.models import Booking, Cart, ShopItem, Ticket
from shop.serializers.item_serializers import (
    BookInfoWithClientSerializer,
    IsActiveTicketSerializer,
)
from shop.services.booking_services import BookingService
from shop.services.cart_services import CartService
from shop.services.item_services import ShopItemService
from shop.services.ticket_services import TicketService
from transactions.models import (
    Balance,
    PayoutSystem,
    Recipient,
    Transaction,
    TransactionFile,
)
from transactions.serializers.stats_serializers import (
    BalanceTotalStatsSerializer,
    TotalStatsSerializer,
)
from transactions.serializers.transaction_serializers import (
    ActivateTransactionWithClientSerializer,
    BalanceQueryParamSerializer,
    BalanceWithUnprocessedTransactionCountSerializer,
    BookingTransactionWithClientSerializer,
    CompleteBookingSerializer,
    CompleteSerializer,
    NewInitPaymentSerializer,
    OnlineCompleteSerializer,
    OnlineOfflinePaymentCompleteSerializer,
    OrganizationRentalTransactionWithClientSerializer,
    OrganizationTicketWithClientSerializer,
    PaymentSuccessSerializer,
    PaymentSystemMethodSerializer,
    PayoutSystemSerializer,
    PayoutSystemWithUnprocessedTransactionCountSerializer,
    PreprocessSerializer,
    RecipientGeneralSerializer,
    ResultURLSerializer,
    StartEndDateTransactionSerializer,
    TicketActivateSerializer,
    TicketSerializer,
    TransactionActivateSerializer,
    TransactionDetailSerializer,
    TransactionFilesSerializer,
    TransactionsSerializer,
    TransactionsTicketSerializer,
    TransactionsWithdrawalSerializer,
    TransactionWithClientSerializer,
    TransactionWithdrawalCompleteSerializer,
    TransactionWithdrawalDetailSerializer,
    TransactionWithdrawalSerializer,
    TransactionWithdrawalSwiftSerializer,
    UserInfoBookingSerializer,
    UserInfoTicketSerializer,
    WithdrawalTypeTransactionSerializer,
)
from transactions.services.filters import (
    TransactionFilter,
    TransactionRentalFilter,
    TransactionTicketFilter,
)
from transactions.services.recipient_services import BalanceService, RecipientService
from transactions.services.transaction_services import (
    PaymentSystemMethodService,
    TransactionService,
)
from users.serializers import (
    ProfileBriefWithPhotoSerializer,
    UserInfoSerializer,
    UserShortInfoSerializer,
)
from users.services import UserService


class TransactionPreprocessView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PreprocessSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        client = serializer.validated_data["client"]
        cart = serializer.validated_data.get("cart", None)
        order_comment = serializer.validated_data.get("order_comment", None)

        new_transaction = TransactionService.preprocess_transaction(
            client=client,
            organization=organization,
            cart=cart,
            processed_by=request.user,
            order_comment=order_comment,
        )

        cumulative = (
            OrganizationClientFinancialStatusService.get_client_cumulative_card(
                client=client, organization=organization
            )
        )
        fixed = DiscountCardService.get_fixed_discounts_of_organization(
            organization=organization
        )
        cashback = DiscountCardService.get_cashback_discounts_of_organization(
            organization=organization
        )

        accrued_cashback = (
            OrganizationClientFinancialStatusService.get_client_accrued_cashback(
                client=client, organization=organization
            )
        )

        if cumulative is not None:
            cumulative = DiscountCardBriefSerializer(cumulative).data

        discounted_price = (
            0 if cart is None else CartService.get_total_prices_in_cart(cart=cart)[1]
        )

        data = {
            "transaction_id": new_transaction.id,
            "purchase_id": organization.running_purchase_id,
            "cumulative": cumulative,
            "fixed": DiscountCardBriefSerializer(fixed, many=True).data,
            "cashback": DiscountCardBriefSerializer(cashback, many=True).data,
            "accrued_cashback": accrued_cashback,
            "client": ProfileBriefWithPhotoSerializer(
                client, context={"request": request}
            ).data,
            "cart_amount": discounted_price,
        }

        return Response(data=data, status=status.HTTP_200_OK)


class TransactionBookingPreprocessView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookInfoWithClientSerializer

    def post(self, request, pk):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        rental = ShopItem.objects.get(id=pk)
        start_time = serializer.validated_data["start_time"]
        end_time = serializer.validated_data["end_time"]
        organization = serializer.validated_data["organization"]
        client = serializer.validated_data["client"]
        booking = Booking.objects.create(
            user=request.user,
            item=rental,
            organization=organization,
            start_time=start_time,
            end_time=end_time,
        )

        new_transaction = TransactionService.preprocess_booking_transaction(
            client=client,
            organization=organization,
            booking=booking,
            processed_by=request.user,
        )

        cumulative = (
            OrganizationClientFinancialStatusService.get_client_cumulative_card(
                client=client, organization=organization
            )
        )
        fixed = DiscountCardService.get_fixed_discounts_of_organization(
            organization=organization
        )
        cashback = DiscountCardService.get_cashback_discounts_of_organization(
            organization=organization
        )

        accrued_cashback = (
            OrganizationClientFinancialStatusService.get_client_accrued_cashback(
                client=client, organization=organization
            )
        )

        if cumulative is not None:
            cumulative = DiscountCardBriefSerializer(cumulative).data

        discounted_price = (
            0
            if booking is None
            else BookingService.get_total_prices_in_booking(booking=booking)[1]
        )

        data = {
            "transaction_id": new_transaction.id,
            "purchase_id": organization.running_purchase_id,
            "cumulative": cumulative,
            "fixed": DiscountCardBriefSerializer(fixed, many=True).data,
            "cashback": DiscountCardBriefSerializer(cashback, many=True).data,
            "accrued_cashback": accrued_cashback,
            "client": ProfileBriefWithPhotoSerializer(
                client, context={"request": request}
            ).data,
            "cart_amount": discounted_price,
        }

        return Response(data=data, status=status.HTTP_200_OK)


class TransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        TransactionService.complete_transaction(
            transaction_id=serializer.validated_data["transaction_id"],
            processed_by=request.user,
            original_amount=serializer.validated_data["original_amount"],
            discount_percent=serializer.validated_data["discount_percent"],
            source_card=serializer.validated_data["source_card"],
            from_cashback=serializer.validated_data["from_cashback"],
            utc_offset_minutes=serializer.validated_data.get("utc_offset_minutes"),
            cart=serializer.validated_data.get("cart", None),
            coupons_ids=serializer.validated_data.get("coupons_ids", None),
        )

        return Response(
            data={"message": _("Transaction successfully completed")},
            status=status.HTTP_200_OK,
        )


class CashierTransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        TransactionService.complete_transaction_cashier(
            transaction_id=serializer.validated_data["transaction_id"],
            processed_by=request.user,
            original_amount=serializer.validated_data["original_amount"],
            discount_percent=serializer.validated_data["discount_percent"],
            source_card=serializer.validated_data["source_card"],
            from_cashback=serializer.validated_data["from_cashback"],
            utc_offset_minutes=serializer.validated_data.get("utc_offset_minutes"),
            cart=serializer.validated_data.get("cart", None),
            coupons_list=serializer.validated_data.get("coupons_ids", None),
        )

        return Response(
            data={"message": _("Transaction successfully completed")},
            status=status.HTTP_200_OK,
        )


class TransactionPayOfflineView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineOfflinePaymentCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        TransactionService.complete_transaction_offline(
            transaction_id=serializer.validated_data["transaction_id"]
        )

        return Response(
            data={"message": _("Transaction successfully paid!")},
            status=status.HTTP_200_OK,
        )


class TransactionBookingCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CompleteBookingSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        transaction = Transaction.objects.get(
            id=serializer.validated_data["transaction_id"]
        )
        booking = transaction.booking

        TransactionService.complete_booking_transaction(
            transaction_id=serializer.validated_data["transaction_id"],
            processed_by=request.user,
            original_amount=serializer.validated_data["original_amount"],
            discount_percent=serializer.validated_data["discount_percent"],
            source_card=serializer.validated_data["source_card"],
            from_cashback=serializer.validated_data["from_cashback"],
            booking=booking,
        )

        return Response(
            data={"message": _("Transaction successfully completed")},
            status=status.HTTP_200_OK,
        )


class OnlineTransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineCompleteSerializer

    def post(self, request, *args, **kwargs):
        start = time()
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        cached = redis_client.get(serializer.validated_data.get("transaction_id"))

        if cached:
            return Response(
                data={"message": _("Transaction successfully completed")},
                status=status.HTTP_200_OK,
            )

        TransactionService.complete_online_transaction(
            transaction_id=serializer.validated_data["transaction_id"],
            utc_offset_minutes=serializer.validated_data.get("utc_offset_minutes"),
            processed_by=request.user,
            request=request,
        )
        total_time = time() - start
        print(f"[TOTAL VIEW TIME]: {total_time:.4f} sec")
        return Response(
            data={"message": _("Transaction successfully completed")},
            status=status.HTTP_200_OK,
        )


class WithdrawalTransactionReviewView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        transaction = TransactionService.review_withdrawal_transaction(
            transaction_id=serializer.validated_data["transaction_id"],
            utc_offset_minutes=serializer.validated_data.get("utc_offset_minutes"),
            processed_by=request.user,
        )

        data = TransactionWithdrawalDetailSerializer(
            transaction, context={"request": request}
        ).data
        return Response(data)


class TransactionFilesCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)
    serializer_class = TransactionFilesSerializer
    queryset = TransactionFile.objects.all()


class WithdrawalTransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithdrawalCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        files = serializer.validated_data.get("files", [])
        comment = serializer.validated_data.get("comment", None)
        transaction = TransactionService.complete_review_withdrawal_transaction(
            transaction_id=serializer.validated_data["transaction_id"],
            files=files,
            comment=comment,
            processed_by=request.user,
            utc_offset_minutes=serializer.validated_data.get("utc_offset_minutes"),
        )

        data = TransactionWithdrawalDetailSerializer(
            transaction, context={"request": request}
        ).data
        return Response(data)


class WithdrawalTransactionDeclineView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithdrawalCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        files = serializer.validated_data.get("files", [])
        comment = serializer.validated_data.get("comment", None)
        transaction = TransactionService.decline_review_withdrawal_transaction(
            transaction_id=serializer.validated_data["transaction_id"],
            files=files,
            comment=comment,
            processed_by=request.user,
            utc_offset_minutes=serializer.validated_data.get("utc_offset_minutes"),
        )

        data = TransactionWithdrawalDetailSerializer(
            transaction, context={"request": request}
        ).data
        return Response(data)


class OnlinePaymentTransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        TransactionService.complete_online_payment_transaction(
            transaction_id=serializer.validated_data["transaction_id"],
            utc_offset_minutes=serializer.validated_data.get("utc_offset_minutes"),
            processed_by=request.user,
            request=request,
        )

        return Response(
            data={"message": _("Transaction successfully completed")},
            status=status.HTTP_200_OK,
        )


class OnlineBookingTransactionCompleteView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        TransactionService.complete_booking_online_transaction(
            transaction_id=serializer.validated_data["transaction_id"],
            utc_offset_minutes=serializer.validated_data.get("utc_offset_minutes"),
            processed_by=request.user,
            request=request,
        )

        return Response(
            data={"message": _("Transaction successfully completed")},
            status=status.HTTP_200_OK,
        )


class UserTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        return TransactionService.get_user_transaction_organizations(
            client=self.request.user,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )


class UserWithdrawalTransactionOrganizationView(ListAPIView):
    serializer_class = (
        PartnerWithWithdrawalLatestTransactionUnprocessedTransactionCountSerializer
    )
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = WithdrawalTypeTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        return TransactionService.get_user_withdrawal_transaction_organizations(
            user=self.request.user,
            withdrawal_type=serializer.validated_data["withdrawal_type"],
        )


class UserSaleTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionUnprocessedTransactionCountSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        return TransactionService.get_user_sale_transaction_organizations(
            user=self.request.user,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )


class UserRentalTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        return TransactionService.get_user_rental_transaction_organizations(
            client=self.request.user,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )


class UserTicketTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        return TransactionService.get_user_ticket_transaction_organizations(
            client=self.request.user,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )


class UserSaleRentalTransactionOrganizationView(ListAPIView):
    serializer_class = PartnerWithLatestTransactionUnprocessedTransactionCountSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        return TransactionService.get_user_sale_rental_transaction_organizations(
            user=self.request.user,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )


class UserSaleTicketTransactionOrganizationView(ListAPIView):
    serializer_class = (
        PartnerWithTicketLatestTransactionUnprocessedTransactionCountSerializer
    )
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        return TransactionService.get_user_sale_ticket_transaction_organizations(
            user=self.request.user,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )


class UserTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get("HTTP_CURRENCY", settings.APP_BASE_CURRENCY)

        totals = TransactionService.get_user_totals(
            client=request.user,
            currency=currency,
            organization=organization,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )
        totals["total_savings"] += totals["total_from_cashback"]
        data = TotalStatsSerializer(totals).data
        return Response(data)


class UserBalanceTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        currency_code = settings.APP_BASE_CURRENCY

        balances = []

        for currency in [Balance.KGS, Balance.TRC]:
            totals = TransactionService.get_user_balance_totals(
                currency=currency_code,
                balance_currency=currency,
                organization=organization,
                start_date=serializer.validated_data.get("start"),
                end_date=serializer.validated_data.get("end"),
            )
            withdrawal_totals = (
                TransactionService.get_organization_processed_withdrawals(
                    currency=currency_code,
                    balance_currency=currency,
                    organization=organization,
                    start_date=serializer.validated_data.get("start"),
                    end_date=serializer.validated_data.get("end"),
                )
            )
            totals = totals - withdrawal_totals

            balance, created = Balance.objects.get_or_create(
                organization=organization, currency=currency
            )
            balance.balance_amount = totals
            balance.save()

            balances.append(balance)

        serializer = BalanceTotalStatsSerializer(balances, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserBalanceDetailTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    # TODO: make separate balance for every payment system
    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        currency_code = settings.APP_BASE_CURRENCY

        balance = BalanceService.get(id=kwargs["pk"])
        currency = balance.currency

        totals = TransactionService.get_user_balance_totals(
            currency=currency_code,
            balance_currency=currency,
            organization=organization,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )
        withdrawal_totals = TransactionService.get_organization_processed_withdrawals(
            currency=currency_code,
            balance_currency=currency,
            organization=organization,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )
        totals = totals - withdrawal_totals
        balance.balance_amount = totals
        balance.save()

        serializer = BalanceTotalStatsSerializer(balance)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PayoutSystemListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PayoutSystemWithUnprocessedTransactionCountSerializer

    def get_queryset(self):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        balance = serializer.validated_data["balance"]
        return balance.payout_systems.all().exclude(name="Swift")


class SwiftPayoutSystemAPIView(APIView):
    def get(self, request, format=None):
        swift_payout = PayoutSystem.objects.filter(name="Swift").first()
        if swift_payout:
            serializer = PayoutSystemSerializer(swift_payout)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "Swift PayoutSystem not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class PayoutSystemDetailAPIView(RetrieveAPIView):
    queryset = PayoutSystem.objects.all()
    serializer_class = PayoutSystemSerializer


class UserSaleTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get("HTTP_CURRENCY", settings.APP_BASE_CURRENCY)

        totals = TransactionService.get_user_sale_totals(
            processed_by=request.user,
            currency=currency,
            organization=organization,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )
        totals["total_savings"] += totals["total_from_cashback"]
        data = TotalStatsSerializer(totals).data
        return Response(data)


class UserRentalTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get("HTTP_CURRENCY", settings.APP_BASE_CURRENCY)
        totals = TransactionService.get_user_rental_totals(
            client=request.user,
            currency=currency,
            organization=organization,
            item=serializer.validated_data.get("item"),
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )
        totals["total_savings"] += totals["total_from_cashback"]
        data = TotalStatsSerializer(totals).data
        return Response(data)


class UserTicketTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get("HTTP_CURRENCY", settings.APP_BASE_CURRENCY)
        totals = TransactionService.get_user_ticket_totals(
            client=request.user,
            currency=currency,
            organization=organization,
            item=serializer.validated_data.get("item"),
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )
        totals["total_savings"] += totals["total_from_cashback"]
        data = TotalStatsSerializer(totals).data
        return Response(data)


class UserSaleRentalTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get("HTTP_CURRENCY", settings.APP_BASE_CURRENCY)

        item = serializer.validated_data["item"]
        totals = TransactionService.get_user_sale_rental_totals(
            processed_by=request.user,
            currency=currency,
            organization=organization,
            item=item,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )
        totals["total_savings"] += totals["total_from_cashback"]
        data = TotalStatsSerializer(totals).data
        return Response(data)


class UserSaleTicketTotalsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        if organization is not None:
            currency = organization.currency.code
        else:
            currency = request.META.get("HTTP_CURRENCY", settings.APP_BASE_CURRENCY)

        item = serializer.validated_data["item"]
        totals = TransactionService.get_user_sale_ticket_totals(
            processed_by=request.user,
            currency=currency,
            organization=organization,
            item=item,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )
        totals["total_savings"] += totals["total_from_cashback"]
        data = TotalStatsSerializer(totals).data
        return Response(data)


class UserTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ["id"]

    def get_queryset(self):
        transactions = TransactionService.get_user_transactions(
            client=self.request.user,
        )
        return transactions


class UserSaleTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ["id"]

    def get_queryset(self):
        transactions = TransactionService.get_user_sale_transactions(
            user=self.request.user
        )
        return transactions


class UserRentalSaleTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ["id"]

    def get_queryset(self):
        transactions = TransactionService.get_user_rental_sale_transactions(
            user=self.request.user
        )
        return transactions


class UserTicketSaleTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsTicketSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ["id"]

    def get_queryset(self):
        transactions = TransactionService.get_user_ticket_sale_transactions(
            user=self.request.user
        )
        return transactions


class UserSaleTransactionsDetailListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionRentalFilter
    search_fields = ["id"]

    def get_queryset(self):
        item = ShopItemService.get(id=self.kwargs["pk"])
        transactions = TransactionService.get_user_sale_transactions_detail(
            user=self.request.user, item=item
        )
        return transactions


class UserSaleTicketTransactionsDetailListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsTicketSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionTicketFilter
    search_fields = ["id"]

    def get_queryset(self):
        item = ShopItemService.get(id=self.kwargs["pk"])
        transactions = TransactionService.get_user_sale_ticket_transactions_detail(
            user=self.request.user, item=item
        )
        return transactions


class UserRentalTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ["id"]

    def get_queryset(self):
        transactions = TransactionService.get_user_rental_transactions(
            client=self.request.user
        )
        return transactions


class UserTicketTransactionsListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ["id"]

    def get_queryset(self):
        transactions = TransactionService.get_user_ticket_transactions(
            client=self.request.user
        )
        return transactions


class UserRentalTransactionsDetailListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionRentalFilter
    search_fields = ["id"]

    def get_queryset(self):
        item = ShopItemService.get(id=self.kwargs["pk"])
        transactions = TransactionService.get_user_rental_transactions_detail(
            client=self.request.user, item=item
        )
        return transactions


class UserTransactionDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        instance = TransactionService.get_transaction(
            transaction_id=pk, requested_by=request.user
        )
        return Response(
            TransactionDetailSerializer(
                instance, context={"request": request, "user": request.user}
            ).data
        )


class OrganizationTransactionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    queryset = Transaction.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = OrganizationTransactionsQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        if not OrganizationService.user_can_see_stats(
            organization=serializer.validated_data["organization"], user=request.user
        ):
            raise NotAcceptableException(_("No rights to see stats of organization"))

        queryset = TransactionService.get_organization_transactions(
            organization=serializer.validated_data["organization"],
            processed_by=serializer.validated_data["processed_by"],
            start_date=serializer.validated_data["start"],
            end_date=serializer.validated_data["end"],
            search_id=serializer.validated_data["search"],
            client=serializer.validated_data["client"],
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrganizationBalanceTransactionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsWithdrawalSerializer
    queryset = Transaction.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = OrganizationTransactionsQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        if not OrganizationService.user_can_see_stats(
            organization=serializer.validated_data["organization"], user=request.user
        ):
            raise NotAcceptableException(_("No rights to see stats of organization"))

        queryset = TransactionService.get_organization_balance_all_transactions(
            organization=serializer.validated_data["organization"],
            start_date=serializer.validated_data["start"],
            end_date=serializer.validated_data["end"],
            search_id=serializer.validated_data["search"],
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrganizationBalanceWithdrawalTransactionListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    queryset = Transaction.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = OrganizationTransactionsQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        if not OrganizationService.user_can_see_stats(
            organization=serializer.validated_data["organization"], user=request.user
        ):
            raise NotAcceptableException(_("No rights to see stats of organization"))

        queryset = TransactionService.get_organization_balance_withdrawal_transactions(
            organization=serializer.validated_data["organization"],
            payout_system=serializer.validated_data["payout_system"],
            start_date=serializer.validated_data["start"],
            end_date=serializer.validated_data["end"],
            search_id=serializer.validated_data["search"],
            status=serializer.validated_data["status"],
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrganizationBalanceListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BalanceWithUnprocessedTransactionCountSerializer
    queryset = Balance.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = OrganizationTransactionsQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        if not OrganizationService.user_can_see_stats(
            organization=serializer.validated_data["organization"], user=request.user
        ):
            raise NotAcceptableException(_("No rights to see stats of organization"))

        queryset = Balance.objects.filter(
            organization=serializer.validated_data["organization"]
        )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TransactionWithdrawalRetrieveView(RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithdrawalDetailSerializer

    def get_object(self):
        return TransactionService.get_transaction(
            transaction_id=self.kwargs["pk"], requested_by=self.request.user
        )


class OrganizationBalanceRecipientListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = RecipientGeneralSerializer
    queryset = Recipient.objects.all()

    def list(self, request, *args, **kwargs):
        serializer = BalanceQueryParamSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        if not OrganizationService.user_can_see_stats(
            organization=serializer.validated_data["organization"], user=request.user
        ):
            raise NotAcceptableException(_("No rights to see stats of organization"))

        queryset = RecipientService.get_organization_balance_recipient(
            balance=serializer.validated_data["balance"]
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
        return TransactionService.get_transaction(
            transaction_id=self.kwargs["pk"], requested_by=self.request.user
        )

    def perform_destroy(self, instance: Transaction):
        # ToDo: implement proper cancellation of transactions
        if not OrganizationService.user_can_see_stats(
            organization=instance.organization, user=self.request.user
        ):
            raise PermissionDeniedException(_("Permission denied"))

        TransactionService.refund_transaction(
            old_transaction=instance, user=self.request.user, request=self.request
        )

        transaction.on_commit(
            lambda: Notification.objects.filter(
                extra_data__transaction_id=instance.id,
                type__in=[
                    NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                    NOTIFICATION_TYPE_AVAILABLE_DELIVERY,
                    NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT,
                ],
            ).delete()
        )


class OrganizationBookingTransactionRetrieveDestroyView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingTransactionWithClientSerializer

    def get_object(self):
        return TransactionService.get_transaction(
            transaction_id=self.kwargs["pk"], requested_by=self.request.user
        )

    def perform_destroy(self, instance: Transaction):
        # ToDo: implement proper cancellation of transactions
        if not OrganizationService.user_can_see_stats(
            organization=instance.organization, user=self.request.user
        ):
            raise PermissionDeniedException(_("Permission denied"))

        TransactionService.refund_booking_transaction(
            old_transaction=instance, user=self.request.user, request=self.request
        )

        transaction.on_commit(
            lambda: Notification.objects.filter(
                extra_data__transaction_id=instance.id,
                type__in=[
                    NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION,
                    NOTIFICATION_TYPE_AVAILABLE_DELIVERY,
                    NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT,
                ],
            ).delete()
        )


class OrgFollowersTransactionsListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsSerializer
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filter_class = TransactionFilter
    search_fields = ["id"]

    def get_queryset(self):
        return TransactionService.get_organization_follower_transactions(
            organization_id=self.kwargs["organization_id"],
            requested_by=self.request.user,
            follower_id=self.kwargs["user_id"],
        )


class UserUnprocessedTransactionCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = TransactionService.get_unprocessed_transactions_count(user=request.user)
        data = dict(count=count)
        return Response(data, status=status.HTTP_200_OK)


class UserWithdrawalTransactionCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = TransactionService.get_withdrawal_unprocessed_transactions_count(
            user=request.user
        )
        data = dict(count=count)
        return Response(data, status=status.HTTP_200_OK)


class UserWithdrawalFundsTransactionCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        payment_system_count = TransactionService.get_payment_system_withdrawal_unprocessed_transactions_count(
            user=request.user
        )
        individual_account_count = (
            TransactionService.get_swift_withdrawal_unprocessed_transactions_count(
                user=request.user
            )
        )
        organization_account_count = 0
        data = dict(
            payment_system_count=payment_system_count,
            individual_account_count=individual_account_count,
            organization_account_count=organization_account_count,
        )
        return Response(data, status=status.HTTP_200_OK)


class UserRentalUnprocessedTransactionCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = TransactionService.get_rental_unprocessed_transactions_count(
            user=request.user
        )
        data = dict(count=count)
        return Response(data, status=status.HTTP_200_OK)


class UserTicketUnprocessedTransactionCountView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        count = TransactionService.get_ticket_unprocessed_transactions_count(
            user=request.user
        )
        data = dict(count=count)
        return Response(data, status=status.HTTP_200_OK)


class OrganizationUsersTransactionView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserShortInfoSerializer
    search_fields = ["full_name", "username"]
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        organization = OrganizationService.get(id=self.kwargs["pk"])
        if not OrganizationService.user_can_see_stats(
            organization=organization, user=self.request.user
        ):
            raise NotAcceptableException(_("No rights to see stats of organization"))
        return TransactionService.get_users_of_transactions_in_organization(
            organization=organization, processed_by=self.request.user
        )


class OrganizationRentalUsersTransactionView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationRentalTransactionWithClientSerializer

    def list(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        rental = ShopItemService.get(id=self.kwargs["pk"])
        queryset = TransactionService.get_organization_processed_transactions(
            rental=rental,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )

        search = self.request.GET.get("search", None)
        if search:
            queryset = TransactionService.get_ordering_search_result(
                queryset=queryset, search_word=search
            )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class OrganizationTicketUsersTransactionView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OrganizationTicketWithClientSerializer

    def list(self, request, *args, **kwargs):
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        ticket = ShopItemService.get(id=self.kwargs["pk"])
        queryset = TransactionService.get_organization_processed_ticket_transactions(
            ticket=ticket,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )

        search = self.request.GET.get("search", None)
        if search:
            queryset = TransactionService.get_ordering_search_result(
                queryset=queryset, search_word=search
            )

        ticket_queryset = Ticket.objects.filter(transaction__in=queryset).order_by(
            "-updated_at"
        )
        page = self.paginate_queryset(ticket_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(ticket_queryset, many=True)
        return Response(serializer.data)


class CheckTicketInUsersView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserInfoTicketSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        ticket = serializer.validated_data["item"]
        client = serializer.validated_data["client"]
        transactions = (
            TransactionService.get_organization_processed_ticket_transactions(
                ticket=ticket
            )
        )
        has_transaction = transactions.filter(client=client).exists()

        return Response(
            data={"has_transaction": has_transaction}, status=status.HTTP_200_OK
        )


class OrganizationRentalCustomerTransactionView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserShortInfoSerializer
    search_fields = ["full_name", "username"]
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        rental = ShopItemService.get(id=self.kwargs["pk"])
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]

        if not OrganizationService.user_can_see_stats(
            organization=organization, user=self.request.user
        ):
            raise NotAcceptableException(_("No rights to see stats of organization"))

        transactions = TransactionService.get_organization_processed_transactions(
            rental=rental,
            start_date=serializer.validated_data.get("start"),
            end_date=serializer.validated_data.get("end"),
        )

        return TransactionService.get_users_of_rental_or_ticket_in_organization(
            transactions
        )


class OrganizationTicketCustomerTransactionView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserShortInfoSerializer
    search_fields = ["full_name", "username"]
    filter_backends = [filters.SearchFilter]

    def get_queryset(self):
        ticket = ShopItemService.get(id=self.kwargs["pk"])
        serializer = StartEndDateTransactionSerializer(data=self.request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]

        if not OrganizationService.user_can_see_stats(
            organization=organization, user=self.request.user
        ):
            raise NotAcceptableException(_("No rights to see stats of organization"))

        transactions = (
            TransactionService.get_organization_processed_ticket_transactions(
                ticket=ticket,
                start_date=serializer.validated_data.get("start"),
                end_date=serializer.validated_data.get("end"),
            )
        )

        return TransactionService.get_users_of_rental_or_ticket_in_organization(
            transactions
        )


class RentPaymentAcceptView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineOfflinePaymentCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        transaction_id = serializer.validated_data["transaction_id"]
        TransactionService.accept_freedompay_booking_transaction_by_user(
            transaction_id=transaction_id, user=self.request.user, request=self.request
        )

        return Response(
            data={"message": _("Transaction successfully paid")},
            status=status.HTTP_200_OK,
        )


class OrderPaymentAcceptView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineOfflinePaymentCompleteSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        transaction_id = serializer.validated_data["transaction_id"]
        TransactionService.accept_freedompay_order_transaction_by_user(
            transaction_id=transaction_id, user=self.request.user
        )

        return Response(
            data={"message": _("Transaction successfully paid")},
            status=status.HTTP_200_OK,
        )


class OrderPaymentRejectView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithClientSerializer

    def get_object(self):
        return TransactionService.get_transaction(
            transaction_id=self.kwargs["pk"], requested_by=self.request.user
        )

    def perform_destroy(self, instance: Transaction):
        TransactionService.reject_order_transaction_by_user(
            old_transaction=instance, user=self.request.user, request=self.request
        )


class RentPaymentRejectView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingTransactionWithClientSerializer

    def get_object(self):
        return TransactionService.get_transaction(
            transaction_id=self.kwargs["pk"], requested_by=self.request.user
        )

    def perform_destroy(self, instance: Transaction):
        TransactionService.reject_booking_transaction_by_user(
            old_transaction=instance, user=self.request.user, request=self.request
        )


class TransactionUserInfoView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ActivateTransactionWithClientSerializer

    def get(self, request, *args, **kwargs):
        serializer = UserInfoBookingSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        booking = serializer.validated_data["booking"]
        client = serializer.validated_data["client"]

        try:
            transaction = Transaction.objects.get(booking=booking)
        except Transaction.DoesNotExist:
            return Response(
                data={"message": _("Transaction not found for this booking")},
                status=status.HTTP_404_NOT_FOUND,
            )

        if transaction.client.id != client.id:
            raise NotAcceptableException(_("Users don't match"))

        serializer = self.get_serializer(transaction)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class TransactionTicketUserInfoView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = IsActiveTicketSerializer

    def get(self, request, *args, **kwargs):
        serializer = UserInfoTicketSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        ticket = serializer.validated_data["item"]
        client = serializer.validated_data["client"]

        tickets = Ticket.objects.filter(item=ticket, user=client).order_by(
            "-updated_at"
        )

        page = self.paginate_queryset(tickets)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
        else:
            serializer = self.get_serializer(tickets, many=True)

        response_data = {
            "client": UserInfoSerializer(client).data,
            "tickets": serializer.data,
        }

        return self.get_paginated_response(response_data)


class TransactionOwnTicketInfoView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = IsActiveTicketSerializer

    def get(self, request, *args, **kwargs):
        serializer = UserInfoTicketSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        ticket = serializer.validated_data["item"]

        queryset = Ticket.objects.filter(item=ticket, user=request.user).order_by(
            "-updated_at"
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TransactionTicketInfoView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionsTicketSerializer

    def get(self, request, *args, **kwargs):
        serializer = TicketSerializer(data=request.GET)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        ticket = serializer.validated_data["ticket"]

        # tickets = Ticket.objects.filter(id=, user=request.user).order_by('-updated_at')
        transaction = TransactionService.get(ticket=ticket)
        serializer = self.get_serializer(transaction)

        return Response(data=serializer.data, status=status.HTTP_200_OK)


class TransactionBookingActivate(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionActivateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        TransactionService.activate_rental(serializer.validated_data["transaction"])

        return Response({"message": "Booking activated successfully"})


class TransactionTicketActivate(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketActivateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        TicketService.activate_ticket(serializer.validated_data["ticket"])

        return Response({"message": "Ticket activated successfully"})


class InitPaymentView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineOfflinePaymentCompleteSerializer
    """
    1 - FreedomPay
    2 - PaySy
    3 - Libersave
    4 - Betapay
    5 - CryptoCloud
    6 - MaalyPay
    7 - ZinaPay
    """

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        base_url = "https://test.apofiz.com/api/v1/"

        if "localhost" in request.META["HTTP_HOST"]:
            base_url = "http://localhost:8000/api/v1/"
        elif "test.apofiz.com" in request.META["HTTP_HOST"]:
            base_url = "https://test.apofiz.com/api/v1/"
        elif "apofiz.com" in request.META["HTTP_HOST"]:
            base_url = "https://apofiz.com/api/v1/"
        if kwargs["pk"] == 1:
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )
            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="KGS",
                amount=transaction.final_amount,
            )
            pg_description, purchase_type = (
                TransactionService.get_pg_description_and_purchase_type(
                    transaction=transaction
                )
            )
            pg_result_url = TransactionService.get_pg_result_url(request=request)
            pg_success_url = TransactionService.get_success_url(request=request)
            pg_failure_url = TransactionService.get_failure_url(request=request)

            payment_data = {
                "pg_order_id": str(transaction_id),
                "pg_merchant_id": FREEDOMPAY_PROJECT_ID,
                "pg_amount": str(converted_amount),
                "pg_description": pg_description,
                "pg_salt": "apofiz",
                "pg_currency": "KGS",
                # 'pg_testing_mode': '1',
                "pg_result_url": pg_result_url,
                "pg_success_url": pg_success_url,
                "pg_failure_url": pg_failure_url,
                "pg_timeout_after_payment": "5",
                "user_id": str(self.request.user.id),
                "purchase_type": purchase_type,
            }

            request_for_signature = TransactionService.make_flat_params_array(
                payment_data
            )
            sorted_params = sorted(request_for_signature.items(), key=lambda x: x[0])
            signature_params = (
                ["init_payment.php"]
                + [str(value) for __, value in sorted_params]
                + [FREEDOMPAY_RECEIVE_SECRET]
            )
            signature = hashlib.md5(";".join(signature_params).encode()).hexdigest()
            payment_data["pg_sig"] = signature
            response = requests.post(
                "https://api.freedompay.money/init_payment.php", data=payment_data
            )
            xml_data = response.text
            response_dict = xmltodict.parse(xml_data)
            json_string = json.dumps(response_dict)
            json_data = json.loads(json_string)
            redirect_url = json_data["response"]["pg_redirect_url"]
            response_data = {"redirect_url": redirect_url}
            return Response(data=response_data, status=status.HTTP_200_OK)
        elif kwargs["pk"] == 2:
            if base_url == "https://apofiz.com/api/v1/":
                currency = "USDT"
                chain_id = 56
                url = "https://api.paysy.net/orders/create_order"
                redirect_url = "https://paysy.net/en/orders/"
            else:
                currency = "USDT"
                chain_id = 5
                url = "https://devnet-api.paysy.net/orders/create_order"
                redirect_url = "https://devnet.paysy.net/en/orders/"
            # currency, chain_id = self.get_company_info(base_url=base_url)
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )
            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="USD",
                amount=transaction.final_amount,
            )
            converted_amount = Decimal(str(converted_amount))
            increase = converted_amount * Decimal("0.02")
            converted_amount += increase
            converted_amount = converted_amount.quantize(
                Decimal("0.00"), rounding=ROUND_DOWN
            )

            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
                transaction=transaction
            )
            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)
            webhook = TransactionService.get_webhook_paysy(request=request)
            params = {
                "currency": currency,
                "chain_id": chain_id,
                "amount": str(converted_amount),
                "is_validation": False,
                "any_key": str(self.request.user.id) + "|" + str(transaction_id),
                "description": purchase_type,
                "success_url": success_url,
                "failure_url": failure_url,
                "webhook": webhook,
                "lang": "en",
                # 'is_redirect': True
            }
            headers = {
                "accept": "application/json",
                "X-API-Key": PAYSY_API_KEY,
                "Content-Type": "application/json",
            }
            response = requests.post(url, headers=headers, params=params)
            response_json = response.json()

            order_id = response_json.get("result", {}).get("id")
            if order_id:
                redirect_url = redirect_url + order_id
                return Response(
                    data={"redirect_url": redirect_url}, status=status.HTTP_200_OK
                )
        elif kwargs["pk"] == 3:
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )

            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
                transaction=transaction
            )

            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="EUR",
                amount=transaction.final_amount,
            )
            if transaction.currency.code != "EUR":
                converted_amount = Decimal(str(converted_amount))
                increase = converted_amount * Decimal("0.01")
                converted_amount += increase
                converted_amount = converted_amount.quantize(
                    Decimal("0.00"), rounding=ROUND_DOWN
                )
            success_url = TransactionService.get_success_url(request=request)
            callback_url = f"{base_url}transactions/result/libersave/"
            currency = "EUR"
            url = "https://api.libersave.com/api/mc/payment"
            amount_float = float(converted_amount)
            if amount_float < 1:
                amount_float = 1
            data = {
                "amount": amount_float,
                "order_id": str(self.request.user.id)
                + "|"
                + str(transaction_id)
                + "|"
                + str(purchase_type),
                "currency": currency,
                "redirect_url": success_url + f"/?transaction_id={transaction_id}",
                "callback_url": callback_url,
            }
            headers = {
                "accept": "application/json",
                "x-api-key": LIBERSAVE_API_KEY,
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            redirect_url = response_json.get("pay_url")
            response_data = {"redirect_url": redirect_url}
            return Response(data=response_data, status=status.HTTP_200_OK)
        elif kwargs["pk"] == 4:
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )
            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="EUR",
                amount=transaction.final_amount,
            )
            if transaction.currency.code != "EUR":
                converted_amount = Decimal(str(converted_amount))
                increase = converted_amount * Decimal("0.01")
                converted_amount += increase
                converted_amount = converted_amount.quantize(
                    Decimal("0.00"), rounding=ROUND_DOWN
                )
            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)
            webhook = TransactionService.get_webhook_betapay(request=request)
            pg_description, purchase_type = (
                TransactionService.get_pg_description_and_purchase_type(
                    transaction=transaction
                )
            )
            currency = "EUR"
            url = "https://api.betapay.online/api/v3/openbanking-payment"
            amount_float = float(converted_amount)
            if amount_float < 10:
                amount_float = 10
            data = {
                "merchant_id": 591,
                "terminal_id": 619,
                "order_id": str(self.request.user.id)
                + "|"
                + str(transaction_id)
                + "|"
                + str(purchase_type),
                "amount": amount_float,
                "currency_code": currency,
                "callback_url": webhook,
                "success_url": success_url,
                "fail_url": failure_url,
            }
            headers = {"token": BETAPAY_API_TOKEN}
            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()

            # redirect_url = response_json.get('data', {}).get('"iframe_url":')
            status_code = response_json.get("status", {}).get("code")
            status_type = response_json.get("status", {}).get("type")
            data_transaction_id = response_json.get("data", {}).get("transaction_id")
            if status_code == 200 and status_type == "success":
                url = "https://api.betapay.online/api/v3/openbanking-payment-test"
                data = {
                    "merchant_id": 591,
                    "terminal_id": 619,
                    "transaction_id": data_transaction_id,
                    "case": "approved",
                }
                headers = {"token": BETAPAY_API_TOKEN}
                response = requests.post(url, headers=headers, json=data)
                response_json2 = response.json()
                status_code2 = response_json2.get("status", {}).get("code")
                data_status = response_json2.get("data", {}).get("status")
                if status_code2 == 200 and data_status == "OK":
                    redirect_url = success_url
                    response_data = {"redirect_url": redirect_url}
                    return Response(data=response_data, status=status.HTTP_200_OK)
                else:
                    redirect_url = failure_url
                    response_data = {"redirect_url": redirect_url}
                    return Response(data=response_data, status=status.HTTP_200_OK)
        elif kwargs["pk"] == 5:
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )
            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="USD",
                amount=transaction.final_amount,
            )
            converted_amount = Decimal(str(converted_amount))
            increase = converted_amount * Decimal("0.01")
            converted_amount += increase
            converted_amount = converted_amount.quantize(
                Decimal("0.00"), rounding=ROUND_DOWN
            )
            pg_description, purchase_type = (
                TransactionService.get_pg_description_and_purchase_type(
                    transaction=transaction
                )
            )
            currency = "USD"
            url = "https://api.cryptocloud.plus/v2/invoice/create"
            amount_float = float(converted_amount)
            postback_url = f"{base_url}transactions/result/cryptocloud/"
            data = {
                "shop_id": CRYPTOCLOUD_SHOP_ID,
                "amount": amount_float,
                "currency": currency,
                "order_id": str(self.request.user.id)
                + "|"
                + str(transaction_id)
                + "|"
                + str(purchase_type),
                "email": self.request.user.email,
                "postback_url": postback_url,
            }
            print(data)
            headers = {"Authorization": f"Token {CRYPTOCLOUD_API_KEY}"}
            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            if response.status_code == 200:
                redirect_url = response_json.get("result", {}).get("link")
                response_data = {"redirect_url": redirect_url}
                return Response(data=response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    data={"error": "Something went wrong"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif kwargs["pk"] == 6:
            transaction_id = serializer.validated_data["transaction_id"]

            print(f"[MaalyPay] Starting payment for transaction_id={transaction_id}")

            try:
                transaction = TransactionService.get(
                    id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
                )
            except Exception as e:
                print(f"[MaalyPay] Error getting transaction: {e}")
                tx = Transaction.objects.filter(id=transaction_id).first()
                if tx:
                    print(f"[MaalyPay] Transaction {transaction_id} exists but not available:")
                    print(f"[MaalyPay]   status={tx.status}, is_processed={tx.is_processed}")
                    if tx.is_processed:
                        return Response(
                            data={"error": "Эта транзакция уже оплачена"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        return Response(
                            data={"error": f"Транзакция недоступна для оплаты (статус: {tx.status})"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    print(f"[MaalyPay] Transaction {transaction_id} not found")
                    return Response(
                        data={"error": "Транзакция не найдена"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            print(f"[MaalyPay] Got transaction: status={transaction.status}, is_processed={transaction.is_processed}")

            # Получаем purchase_type для callback обработки
            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
                transaction=transaction
            )

            # Получаем имя клиента
            client_name = (
                transaction.client.full_name
                or f"{transaction.client.first_name or ''} {transaction.client.last_name or ''}".strip()
                or "Клиент"
            )
            order_number = f"№{transaction_id}"
            org_title = transaction.organization.title if transaction.organization else ""

            # Build MaalyPay description based on whether cart exists
            try:
                cart = transaction.cart
                cart_items = cart.items.all()
                if cart_items.exists():
                    # Формируем описание: Org • №ID • Client | товары
                    header = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")
                    items_list = ", ".join(
                        f"{item.item.name} x{item.count}" for item in cart_items
                    )
                    maalypay_description = f"{header} | {items_list}"
                else:
                    maalypay_description = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")
            except (Cart.DoesNotExist, AttributeError):
                maalypay_description = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")

            if not transaction.organization:
                return Response(
                    data={"error": "Transaction organization is not set"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment_config = MaalyPayService.get_config(transaction.organization)

            if not payment_config:
                return Response(
                    data={"error": "MaalyPay is not configured for this organization"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            merchant_tx_id = MaalyPayService.generate_merchant_tx_id(transaction.pk)
            callback_url = f"{base_url}transactions/maalypay/result/?tx={transaction.pk}"

            print(f"[MaalyPay VIEW] merchant_tx_id={merchant_tx_id}")
            print(f"[MaalyPay VIEW] transaction.pk={transaction.pk}, status={transaction.status}, is_processed={transaction.is_processed}")

            # Получаем URL для редиректа (на основе текущего request)
            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)

            # Сохраняем purchase_type, user_id и URL редиректа в payment_info
            transaction.payment_info = json.dumps({
                "purchase_type": purchase_type,
                "user_id": self.request.user.id,
                "merchant_tx_id": merchant_tx_id,
                "success_url": success_url,
                "failure_url": failure_url,
            })
            transaction.save(update_fields=["payment_info"])

            print(f"[MaalyPay VIEW] Calling create_payment with amount={transaction.final_amount}, currency={transaction.currency.code}")

            checkout_url = MaalyPayService.create_payment(
                api_key=payment_config.api_key,
                merchant_id=int(payment_config.merchant_id),
                amount=str(transaction.final_amount),
                currency=transaction.currency.code,
                description=maalypay_description,
                merchant_tx_id=merchant_tx_id,
                callback_url=callback_url,
                customer_email=transaction.client.email or "noemail@placeholder.local",
                bank_info=payment_config.bank_info,
            )

            print(f"[MaalyPay VIEW] checkout_url result: {checkout_url}")

            if not checkout_url:
                return Response(
                    data={
                        "error": "Failed to create MaalyPay payment. Please try again."
                    },
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            fetch_maalypay_status.delay(
                merchant_tx_id=merchant_tx_id,
                api_key=payment_config.api_key,
                transaction_id=transaction.pk,
                purchase_type=purchase_type,
                user_id=self.request.user.id,
            )

            return Response(
                data={"redirect_url": checkout_url},
                status=status.HTTP_200_OK,
            )

        elif kwargs["pk"] == 7:
            # ZinaPay
            from organizations.services.zinapay_service import ZinaPayService

            transaction_id = serializer.validated_data["transaction_id"]
            print(f"\n{'='*60}")
            print("[ZinaPay DEBUG] === INIT PAYMENT START ===")
            print(f"[ZinaPay DEBUG] transaction_id={transaction_id}")
            print(f"[ZinaPay DEBUG] base_url={base_url}")

            try:
                transaction = TransactionService.get(
                    id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
                )
            except Exception:
                tx = Transaction.objects.filter(id=transaction_id).first()
                if tx:
                    if tx.is_processed:
                        return Response(
                            data={"error": "This transaction is already paid"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        return Response(
                            data={"error": f"Transaction not available for payment (status: {tx.status})"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    return Response(
                        data={"error": "Transaction not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            if not transaction.organization:
                return Response(
                    data={"error": "Transaction organization is not set"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            config = ZinaPayService.get_config(transaction.organization)
            print(f"[ZinaPay DEBUG] org_id={transaction.organization.id}, org_title={transaction.organization.title}")
            print(f"[ZinaPay DEBUG] config found: {config is not None}")
            if config:
                print(f"[ZinaPay DEBUG] api_token: {config.api_token[:20]}...")

            if not config:
                print("[ZinaPay DEBUG] ERROR: ZinaPay not configured!")
                return Response(
                    data={"error": "ZinaPay is not configured for this organization"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            print(f"[ZinaPay DEBUG] currency={transaction.currency.code}, amount={transaction.final_amount}")

            try:
                ZinaPayService.validate_currency(transaction.currency.code)
                print("[ZinaPay DEBUG] currency validation: OK")
            except BadRequestException as e:
                print(f"[ZinaPay DEBUG] ERROR: currency validation failed: {e}")
                return Response(
                    data={"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
                transaction=transaction
            )
            print(f"[ZinaPay DEBUG] purchase_type={purchase_type}")

            # Build detailed payment description
            client_name = (
                transaction.client.full_name
                or f"{transaction.client.first_name or ''} {transaction.client.last_name or ''}".strip()
                or "Client"
            )
            order_number = f"#{transaction.id}"
            org_title = transaction.organization.title if transaction.organization else ""

            # Try to include cart items in description
            try:
                cart = transaction.cart
                cart_items = cart.items.all()
                if cart_items.exists():
                    header = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")
                    items_list = ", ".join(
                        f"{item.item.name} x{item.count}" for item in cart_items
                    )
                    message = f"{header} | {items_list}"
                else:
                    message = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")
            except (Cart.DoesNotExist, AttributeError):
                message = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")

            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)
            callback_url = f"{base_url}transactions/zinapay/result/?tx={transaction.id}"

            print(f"[ZinaPay DEBUG] success_url={success_url}")
            print(f"[ZinaPay DEBUG] failure_url={failure_url}")
            print(f"[ZinaPay DEBUG] callback_url={callback_url}")

            amount_fils = ZinaPayService.convert_to_fils(
                transaction.final_amount,
                transaction.currency.code
            )
            print(f"[ZinaPay DEBUG] amount_fils={amount_fils} (original: {transaction.final_amount})")
            print(f"[ZinaPay DEBUG] message={message}")

            print("[ZinaPay DEBUG] Calling ZinaPay API create_payment_intent...")
            result = ZinaPayService.create_payment_intent(
                api_token=config.api_token,
                amount=amount_fils,
                currency_code=transaction.currency.code,
                success_url=callback_url,
                cancel_url=callback_url,
                failure_url=callback_url,
                message=message,
            )

            if not result:
                print("[ZinaPay DEBUG] ERROR: create_payment_intent returned None!")
                return Response(
                    data={"error": "Failed to create ZinaPay payment. Please try again."},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            print("[ZinaPay DEBUG] ZinaPay API response:")
            print(f"[ZinaPay DEBUG]   payment_intent_id={result.get('id')}")
            print(f"[ZinaPay DEBUG]   redirect_url={result.get('redirect_url')}")
            print(f"[ZinaPay DEBUG]   status={result.get('status')}")

            transaction.payment_info = {
                "payment_mode": ZinaPayService.MODE_P2P,
                "purchase_type": purchase_type,
                "user_id": self.request.user.id,
                "zinapay_payment_intent_id": result["id"],
                "success_url": success_url,
                "failure_url": failure_url,
            }
            transaction.save(update_fields=["payment_info"])

            print("[ZinaPay DEBUG] Transaction payment_info saved")
            print("[ZinaPay DEBUG] === INIT PAYMENT SUCCESS ===")
            print(f"{'='*60}\n")

            return Response(
                data={"redirect_url": result["redirect_url"]},
                status=status.HTTP_200_OK,
            )
        elif kwargs["pk"] == 8:
            transaction_id = serializer.validated_data["transaction_id"]
            print(f"\n{'='*60}")
            print("[Profitgate DEBUG] === INIT PAYMENT START ===")
            print(f"[Profitgate DEBUG] transaction_id={transaction_id}")

            try:
                transaction = TransactionService.get(
                    id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
                )
            except Exception:
                tx = Transaction.objects.filter(id=transaction_id).first()
                if tx:
                    if tx.is_processed:
                        return Response(data={"error": "Эта транзакция уже оплачена"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return Response(data={"error": f"Транзакция недоступна (статус: {tx.status})"}, status=status.HTTP_400_BAD_REQUEST)
                return Response(data={"error": "Транзакция не найдена"}, status=status.HTTP_404_NOT_FOUND)

            if not transaction.organization:
                return Response(data={"error": "У транзакции не указана организация"}, status=status.HTTP_400_BAD_REQUEST)

            integration = ProfitgateOrganizationPaymentSystem.objects.filter(
                organization=transaction.organization, is_active=True
            ).first()

            if not integration:
                return Response(data={"error": "Profitgate не настроен"}, status=status.HTTP_400_BAD_REQUEST)

            # 1. Проверяем, разрешил ли админ принимать эту оригинальную валюту (например, AED)
            if not integration.currencies.filter(code=transaction.currency.code).exists():
                print(f"[Profitgate DEBUG] ERROR: Currency {transaction.currency.code} not allowed.")
                return Response(
                    data={"error": f"Оплата через Profitgate в валюте {transaction.currency.code} не поддерживается. Добавьте её в админке."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            target_currency = "RUB"
            if transaction.currency.code != target_currency:
                print(f"[Profitgate DEBUG] Converting {transaction.final_amount} {transaction.currency.code} to {target_currency}")
                
                converted_amount = CurrencyConverterService.convert(
                    from_currency=transaction.currency.code,
                    to_currency=target_currency,
                    amount=transaction.final_amount,
                )
                converted_amount = Decimal(str(converted_amount)).quantize(
                    Decimal("0.00"), rounding=ROUND_DOWN
                )
            else:
                converted_amount = transaction.final_amount
                
            print(f"[Profitgate DEBUG] Final Amount for Gateway: {converted_amount} {target_currency}")

            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(transaction)
            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)
            notification_url = f"{base_url}transactions/webhooks/profitgate/"
            
            service = ProfitgateService(integration)

            try:
                redirect_url = service.create_redirect_payment(
                    transaction=transaction,
                    amount=converted_amount,         # <--- Передаем рубли
                    currency_code=target_currency,   # <--- Жестко ставим RUB
                    finish_url=success_url, 
                    notification_url=notification_url
                )
                
                transaction.payment_info = {
                    "purchase_type": purchase_type,
                    "user_id": self.request.user.id,
                    "success_url": success_url,
                    "failure_url": failure_url,
                }
                transaction.save(update_fields=["payment_info"])

                print("[Profitgate DEBUG] === INIT PAYMENT SUCCESS ===")
                print(f"{'='*60}\n")

                return Response(data={"redirect_url": redirect_url}, status=status.HTTP_200_OK)

            except Exception as e:
                print(f"[Profitgate DEBUG] ERROR: {str(e)}")
                return Response(
                    data={"error": "Ошибка инициализации Profitgate", "details": str(e)},
                    status=status.HTTP_502_BAD_GATEWAY,
                )


class NewInitPaymentView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NewInitPaymentSerializer

    """
    1 - FreedomPay
    2 - PaySy
    3 - Libersave
    4 - Betapay
    5 - CryptoCloud
    6 - MaalyPay
    """

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        base_url = "https://test.apofiz.com/api/v1/"

        if "localhost" in request.META["HTTP_HOST"]:
            base_url = "http://localhost:8000/api/v1/"
        elif "test.apofiz.com" in request.META["HTTP_HOST"]:
            base_url = "https://test.apofiz.com/api/v1/"
        elif "apofiz.com" in request.META["HTTP_HOST"]:
            base_url = "https://apofiz.com/api/v1/"
        transaction_id = serializer.validated_data["transaction_id"]
        payment_method_code = serializer.validated_data["payment_method_code"]
        payment_method = PaymentSystemMethodService.get(
            code=payment_method_code, is_active=True
        )

        if payment_method.code == "freedom_pay":
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )
            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="KGS",
                amount=transaction.final_amount,
            )
            pg_description, purchase_type = (
                TransactionService.get_pg_description_and_purchase_type(
                    transaction=transaction
                )
            )
            pg_result_url = TransactionService.get_pg_result_url(request=request)
            pg_success_url = TransactionService.get_success_url(request=request)
            pg_failure_url = TransactionService.get_failure_url(request=request)

            payment_data = {
                "pg_order_id": str(transaction_id),
                "pg_merchant_id": FREEDOMPAY_PROJECT_ID,
                "pg_amount": str(converted_amount),
                "pg_description": pg_description,
                "pg_salt": "apofiz",
                "pg_currency": "KGS",
                # 'pg_testing_mode': '1',
                "pg_result_url": pg_result_url,
                "pg_success_url": pg_success_url,
                "pg_failure_url": pg_failure_url,
                "pg_timeout_after_payment": "5",
                "user_id": str(self.request.user.id),
                "purchase_type": purchase_type,
            }

            request_for_signature = TransactionService.make_flat_params_array(
                payment_data
            )
            sorted_params = sorted(request_for_signature.items(), key=lambda x: x[0])
            signature_params = (
                ["init_payment.php"]
                + [str(value) for __, value in sorted_params]
                + [FREEDOMPAY_RECEIVE_SECRET]
            )
            signature = hashlib.md5(";".join(signature_params).encode()).hexdigest()
            payment_data["pg_sig"] = signature
            response = requests.post(
                "https://api.freedompay.money/init_payment.php", data=payment_data
            )
            xml_data = response.text
            response_dict = xmltodict.parse(xml_data)
            json_string = json.dumps(response_dict)
            json_data = json.loads(json_string)
            redirect_url = json_data["response"]["pg_redirect_url"]
            response_data = {"redirect_url": redirect_url}
            return Response(data=response_data, status=status.HTTP_200_OK)
        elif payment_method.code == "paysy":
            if base_url == "https://apofiz.com/api/v1/":
                currency = "USDT"
                chain_id = 56
                url = "https://api.paysy.net/orders/create_order"
                redirect_url = "https://paysy.net/en/orders/"
            else:
                currency = "USDT"
                chain_id = 5
                url = "https://devnet-api.paysy.net/orders/create_order"
                redirect_url = "https://devnet.paysy.net/en/orders/"
            # currency, chain_id = self.get_company_info(base_url=base_url)
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )
            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="USD",
                amount=transaction.final_amount,
            )
            converted_amount = Decimal(str(converted_amount))
            increase = converted_amount * Decimal("0.02")
            converted_amount += increase
            converted_amount = converted_amount.quantize(
                Decimal("0.00"), rounding=ROUND_DOWN
            )

            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
                transaction=transaction
            )
            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)
            webhook = TransactionService.get_webhook_paysy(request=request)
            params = {
                "currency": currency,
                "chain_id": chain_id,
                "amount": str(converted_amount),
                "is_validation": False,
                "any_key": str(self.request.user.id) + "|" + str(transaction_id),
                "description": purchase_type,
                "success_url": success_url,
                "failure_url": failure_url,
                "webhook": webhook,
                "lang": "en",
                # 'is_redirect': True
            }
            headers = {
                "accept": "application/json",
                "X-API-Key": PAYSY_API_KEY,
                "Content-Type": "application/json",
            }
            response = requests.post(url, headers=headers, params=params)
            response_json = response.json()

            order_id = response_json.get("result", {}).get("id")
            if order_id:
                redirect_url = redirect_url + order_id
                return Response(
                    data={"redirect_url": redirect_url}, status=status.HTTP_200_OK
                )
        elif payment_method.code == "libersave":
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )

            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
                transaction=transaction
            )

            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="EUR",
                amount=transaction.final_amount,
            )
            if transaction.currency.code != "EUR":
                converted_amount = Decimal(str(converted_amount))
                increase = converted_amount * Decimal("0.01")
                converted_amount += increase
                converted_amount = converted_amount.quantize(
                    Decimal("0.00"), rounding=ROUND_DOWN
                )
            success_url = TransactionService.get_success_url(request=request)
            callback_url = f"{base_url}transactions/result/libersave/"
            currency = "EUR"
            url = "https://api.libersave.com/api/mc/payment"
            amount_float = float(converted_amount)
            if amount_float < 1:
                amount_float = 1
            data = {
                "amount": amount_float,
                "order_id": str(self.request.user.id)
                + "|"
                + str(transaction_id)
                + "|"
                + str(purchase_type),
                "currency": currency,
                "redirect_url": success_url + f"/?transaction_id={transaction_id}",
                "callback_url": callback_url,
            }
            headers = {
                "accept": "application/json",
                "x-api-key": LIBERSAVE_API_KEY,
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            redirect_url = response_json.get("pay_url")
            response_data = {"redirect_url": redirect_url}
            return Response(data=response_data, status=status.HTTP_200_OK)
        elif payment_method.code == "betapay":
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )
            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="EUR",
                amount=transaction.final_amount,
            )
            if transaction.currency.code != "EUR":
                converted_amount = Decimal(str(converted_amount))
                increase = converted_amount * Decimal("0.01")
                converted_amount += increase
                converted_amount = converted_amount.quantize(
                    Decimal("0.00"), rounding=ROUND_DOWN
                )
            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)
            webhook = TransactionService.get_webhook_betapay(request=request)
            pg_description, purchase_type = (
                TransactionService.get_pg_description_and_purchase_type(
                    transaction=transaction
                )
            )
            currency = "EUR"
            url = "https://api.betapay.online/api/v3/openbanking-payment"
            amount_float = float(converted_amount)
            if amount_float < 10:
                amount_float = 10
            data = {
                "merchant_id": 591,
                "terminal_id": 619,
                "order_id": str(self.request.user.id)
                + "|"
                + str(transaction_id)
                + "|"
                + str(purchase_type),
                "amount": amount_float,
                "currency_code": currency,
                "callback_url": webhook,
                "success_url": success_url,
                "fail_url": failure_url,
            }
            headers = {"token": BETAPAY_API_TOKEN}
            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()

            # redirect_url = response_json.get('data', {}).get('"iframe_url":')
            status_code = response_json.get("status", {}).get("code")
            status_type = response_json.get("status", {}).get("type")
            data_transaction_id = response_json.get("data", {}).get("transaction_id")
            if status_code == 200 and status_type == "success":
                url = "https://api.betapay.online/api/v3/openbanking-payment-test"
                data = {
                    "merchant_id": 591,
                    "terminal_id": 619,
                    "transaction_id": data_transaction_id,
                    "case": "approved",
                }
                headers = {"token": BETAPAY_API_TOKEN}
                response = requests.post(url, headers=headers, json=data)
                response_json2 = response.json()
                status_code2 = response_json2.get("status", {}).get("code")
                data_status = response_json2.get("data", {}).get("status")
                if status_code2 == 200 and data_status == "OK":
                    redirect_url = success_url
                    response_data = {"redirect_url": redirect_url}
                    return Response(data=response_data, status=status.HTTP_200_OK)
                else:
                    redirect_url = failure_url
                    response_data = {"redirect_url": redirect_url}
                    return Response(data=response_data, status=status.HTTP_200_OK)
        elif payment_method.code == "cryptocloud":
            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )
            converted_amount = CurrencyConverterService.convert(
                from_currency=transaction.currency.code,
                to_currency="USD",
                amount=transaction.final_amount,
            )
            converted_amount = Decimal(str(converted_amount))
            increase = converted_amount * Decimal("0.01")
            converted_amount += increase
            converted_amount = converted_amount.quantize(
                Decimal("0.00"), rounding=ROUND_DOWN
            )
            pg_description, purchase_type = (
                TransactionService.get_pg_description_and_purchase_type(
                    transaction=transaction
                )
            )
            currency = "USD"
            url = "https://api.cryptocloud.plus/v2/invoice/create"
            amount_float = float(converted_amount)
            postback_url = f"{base_url}transactions/result/cryptocloud/"
            data = {
                "shop_id": CRYPTOCLOUD_SHOP_ID,
                "amount": amount_float,
                "currency": currency,
                "order_id": str(self.request.user.id)
                + "|"
                + str(transaction_id)
                + "|"
                + str(purchase_type),
                "email": self.request.user.email,
                "postback_url": postback_url,
            }
            headers = {"Authorization": f"Token {CRYPTOCLOUD_API_KEY}"}
            response = requests.post(url, headers=headers, json=data)
            response_json = response.json()
            if response.status_code == 200:
                redirect_url = response_json.get("result", {}).get("link")
                response_data = {"redirect_url": redirect_url}
                return Response(data=response_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    data={"error": "Something went wrong"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif payment_method.code == "maalypay":
            from organizations.services.maalypay_service import MaalyPayService

            transaction_id = serializer.validated_data["transaction_id"]
            transaction = TransactionService.get(
                id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
            )

            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
                transaction=transaction
            )

            client_name = (
                transaction.client.full_name
                or f"{transaction.client.first_name or ''} {transaction.client.last_name or ''}".strip()
                or "Клиент"
            )
            order_number = f"№{transaction_id}"
            org_title = transaction.organization.title if transaction.organization else ""

            try:
                cart = transaction.cart
                cart_items = cart.items.all()
                if cart_items.exists():
                    header = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")
                    items_list = ", ".join(
                        f"{item.item.name} x{item.count}" for item in cart_items
                    )
                    maalypay_description = f"{header} | {items_list}"
                else:
                    maalypay_description = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")
            except (Cart.DoesNotExist, AttributeError):
                maalypay_description = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")

            if not transaction.organization:
                return Response(
                    data={"error": "Transaction organization is not set"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment_config = MaalyPayService.get_config(transaction.organization)

            if not payment_config:
                return Response(
                    data={"error": "MaalyPay is not configured for this organization"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            merchant_tx_id = MaalyPayService.generate_merchant_tx_id(transaction.pk)
            callback_url = f"{base_url}transactions/maalypay/result/?tx={transaction.pk}"

            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)

            transaction.payment_info = json.dumps({
                "purchase_type": purchase_type,
                "user_id": self.request.user.id,
                "merchant_tx_id": merchant_tx_id,
                "success_url": success_url,
                "failure_url": failure_url,
            })
            transaction.save(update_fields=["payment_info"])

            checkout_url = MaalyPayService.create_payment(
                api_key=payment_config.api_key,
                merchant_id=int(payment_config.merchant_id),
                amount=str(transaction.final_amount),
                currency=transaction.currency.code,
                description=maalypay_description,
                merchant_tx_id=merchant_tx_id,
                callback_url=callback_url,
                customer_email=transaction.client.email or "noemail@placeholder.local",
                bank_info=payment_config.bank_info,
            )

            if not checkout_url:
                return Response(
                    data={"error": "Failed to create MaalyPay payment"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            fetch_maalypay_status.delay(
                merchant_tx_id=merchant_tx_id,
                api_key=payment_config.api_key,
                transaction_id=transaction.pk,
                purchase_type=purchase_type,
                user_id=self.request.user.id,
            )

            return Response(
                data={"redirect_url": checkout_url},
                status=status.HTTP_200_OK,
            )
        elif payment_method.code == "zinapay":
            from organizations.services.zinapay_service import ZinaPayService

            transaction_id = serializer.validated_data["transaction_id"]

            try:
                transaction = TransactionService.get(
                    id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
                )
            except Exception:
                tx = Transaction.objects.filter(id=transaction_id).first()
                if tx:
                    if tx.is_processed:
                        return Response(
                            data={"error": "This transaction is already paid"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        return Response(
                            data={"error": f"Transaction unavailable for payment (status: {tx.status})"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    return Response(
                        data={"error": "Transaction not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )

            if not transaction.organization:
                return Response(
                    data={"error": "Transaction organization is not set"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            config = ZinaPayService.get_config(transaction.organization)
            if not config:
                return Response(
                    data={"error": "ZinaPay is not configured for this organization"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                ZinaPayService.validate_currency(transaction.currency.code)
            except BadRequestException as e:
                return Response(
                    data={"error": str(e)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
                transaction=transaction
            )

            client_name = (
                transaction.client.full_name
                or f"{transaction.client.first_name or ''} {transaction.client.last_name or ''}".strip()
                or "Client"
            )
            order_number = f"#{transaction.id}"
            org_title = transaction.organization.title if transaction.organization else ""

            try:
                cart = transaction.cart
                cart_items = cart.items.all()
                if cart_items.exists():
                    header = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")
                    items_list = ", ".join(
                        f"{item.item.name} x{item.count}" for item in cart_items
                    )
                    message = f"{header} | {items_list}"
                else:
                    message = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")
            except (Cart.DoesNotExist, AttributeError):
                message = f"{org_title} • {order_number} • {client_name}".replace("  ", " ").strip(" •")

            success_url = TransactionService.get_success_url(request=request)
            failure_url = TransactionService.get_failure_url(request=request)

            callback_url = f"{base_url}transactions/zinapay/result/?tx={transaction.id}"

            amount_fils = ZinaPayService.convert_to_fils(
                transaction.final_amount,
                transaction.currency.code
            )

            result = ZinaPayService.create_payment_intent(
                api_token=config.api_token,
                amount=amount_fils,
                currency_code=transaction.currency.code,
                success_url=callback_url,
                cancel_url=callback_url,
                failure_url=callback_url,
                message=message,
            )

            if not result:
                return Response(
                    data={"error": "Failed to create ZinaPay payment"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

            payment_intent_id = result["id"]

            transaction.payment_info = {
                "payment_mode": ZinaPayService.MODE_P2P,
                "purchase_type": purchase_type,
                "user_id": self.request.user.id,
                "zinapay_payment_intent_id": payment_intent_id,
                "success_url": success_url,
                "failure_url": failure_url,
            }
            transaction.save(update_fields=["payment_info"])


            from organizations.tasks import fetch_zinapay_status
            transaction.on_commit(
                lambda: fetch_zinapay_status.delay(
                    transaction_id=transaction.id,
                    payment_intent_id=payment_intent_id
                )
            )

            return Response(
                data={"redirect_url": result["redirect_url"]},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"error": "Payment System Not Found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class InitPaymentSwiftView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = OnlineOfflinePaymentCompleteSerializer

    def get_company_info(self):
        company_info_url = "https://devnet-api.paysy.net/companies/get"

        headers = {"accept": "application/json", "X-API-Key": PAYSY_API_KEY}

        try:
            response = requests.get(company_info_url, headers=headers)
            if response.status_code == 200:
                company_info = response.json().get("result", {})
                if company_info.get("status", False):
                    deposit_info = company_info.get("deposit", {}).get("5", {})
                    currency = deposit_info.get("currency", "USDT")
                    chain_id = deposit_info.get("chain", 5)
                    return currency, chain_id
                else:
                    return None, None

            else:
                return "USDT", 5

        except Exception:
            return "USD", 5

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        currency, chain_id = self.get_company_info()
        if currency is None or chain_id is None:
            return Response(
                data={
                    "message": _("Failed to retrieve company information from PaySy"),
                    "error": _("Company information retrieval failed"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        transaction_id = serializer.validated_data["transaction_id"]
        transaction = TransactionService.get(
            id=transaction_id, is_processed=False, status=Transaction.ACCEPTED
        )
        converted_amount = CurrencyConverterService.convert(
            from_currency=transaction.currency.code,
            to_currency="USD",
            amount=transaction.final_amount,
        )
        converted_amount = Decimal(str(converted_amount))
        increase = converted_amount * Decimal("0.02")
        converted_amount += increase
        converted_amount = converted_amount.quantize(
            Decimal("0.00"), rounding=ROUND_DOWN
        )

        __, purchase_type = TransactionService.get_pg_description_and_purchase_type(
            transaction=transaction
        )
        success_url = TransactionService.get_success_url(request=request)
        failure_url = TransactionService.get_failure_url(request=request)
        webhook = TransactionService.get_webhook_paysy(request=request)
        params = {
            "currency": currency,
            "chain_id": chain_id,
            "amount": str(converted_amount),
            "is_validation": False,
            "any_key": str(self.request.user.id) + "|" + str(transaction_id),
            "description": purchase_type,
            "success_url": success_url,
            "failure_url": failure_url,
            "webhook": webhook,
            "lang": "en",
            # 'is_redirect': True
        }
        headers = {
            "accept": "application/json",
            "X-API-Key": PAYSY_API_KEY,
            "Content-Type": "application/json",
        }
        url = "https://devnet-api.paysy.net/orders/create_order"
        response = requests.post(url, headers=headers, params=params)
        response_json = response.json()

        order_id = response_json.get("result", {}).get("id")
        if order_id:
            redirect_url = f"https://devnet.paysy.net/en/orders/{order_id}"
            return Response(
                data={"redirect_url": redirect_url}, status=status.HTTP_200_OK
            )
        else:
            return Response(
                data={
                    "message": _("Failed to retrieve order ID from PaySy response"),
                    "error": _("Order ID retrieval failed"),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class PaySyWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        payload = request.data
        event_type = payload.get("event")
        order = payload.get("order")
        any_key = order.get("any_key")
        purchase_type = order.get("description")
        user_id, transaction_id = any_key.split("|")

        user_id = int(user_id)
        user = UserService.get(id=user_id)
        transaction_id = int(transaction_id)
        transaction = TransactionService.get(id=transaction_id)

        if event_type == "ORDER_COMPLETED":
            if purchase_type == "product":
                TransactionService.accept_paysy_order_transaction_by_user(
                    transaction_id=transaction.id, user=user
                )

            elif purchase_type == "deal":
                TransactionService.complete_paysy_transaction_online(
                    transaction_id=transaction.id
                )
            elif purchase_type == "assistant":
                TransactionService.accept_assistant_transaction(
                    transaction_id=transaction.id
                )

            else:
                TransactionService.accept_paysy_booking_transaction_by_user(
                    transaction_id=transaction.id, user=user, request=self.request
                )
            response_data = {
                "status": "ok",
            }
            return Response(response_data, status=status.HTTP_200_OK)
        elif event_type == "ORDER_CREATED":
            response_data = {
                "status": "ORDER_CREATED",
            }
            return Response(response_data, status=status.HTTP_200_OK)
        elif event_type == "DEPOSIT_PENDING":
            response_data = {
                "status": "DEPOSIT_PENDING",
            }
            return Response(response_data, status=status.HTTP_200_OK)
        elif event_type == "DEPOSIT_CONFIRMED":
            response_data = {
                "status": "DEPOSIT_CONFIRMED",
            }
            return Response(response_data, status=status.HTTP_200_OK)
        elif event_type == "ORDER_PAYMENT_EXPIRED":
            response_data = {
                "status": "ORDER_PAYMENT_EXPIRED",
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(
            {"message": "Received an unknown event type"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class BetaPayWebhookView(APIView):
    def post(self, request, *args, **kwargs):
        payload = request.data
        order_id = payload.get("order_id")
        user_id, transaction_id, purchase_type = order_id.split("|")
        status_value = payload.get("status")
        error_code = payload.get("error_code")
        error_message = payload.get("error_message")

        user_id = int(user_id)
        user = UserService.get(id=user_id)
        transaction_id = int(transaction_id)
        transaction = TransactionService.get(id=transaction_id)
        if error_code == "":
            if status_value == "approved":
                if purchase_type == "product":
                    TransactionService.accept_paysy_order_transaction_by_user(
                        transaction_id=transaction.id, user=user
                    )

                elif purchase_type == "deal":
                    TransactionService.complete_paysy_transaction_online(
                        transaction_id=transaction.id
                    )
                elif purchase_type == "assistant":
                    TransactionService.accept_assistant_transaction(
                        transaction_id=transaction.id
                    )
                else:
                    TransactionService.accept_paysy_booking_transaction_by_user(
                        transaction_id=transaction.id, user=user, request=self.request
                    )
                response_data = {
                    "status": "ok",
                }
                return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(error_message, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {"message": "Received an unknown status"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class CryptoCloudPostbackView(APIView):
    def post(self, request, *args, **kwargs):
        payload = request.data
        print(f"[CryptoCloud] Webhook received: {payload}")

        order_id = payload.get("order_id")
        if not order_id:
            print(f"[CryptoCloud] ERROR: No order_id in payload")
            return Response({"error": "Missing order_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_id, transaction_id, purchase_type = order_id.split("|")
        except ValueError as e:
            print(f"[CryptoCloud] ERROR: Invalid order_id format: {order_id}, error: {e}")
            return Response({"error": "Invalid order_id format"}, status=status.HTTP_400_BAD_REQUEST)

        status_value = payload.get("status")
        print(f"[CryptoCloud] Processing: user_id={user_id}, transaction_id={transaction_id}, purchase_type={purchase_type}, status={status_value}")

        user_id = int(user_id)
        user = UserService.get(id=user_id)
        transaction_id = int(transaction_id)
        transaction = TransactionService.get(id=transaction_id)
        if status_value == "success":
            if purchase_type == "product":
                TransactionService.accept_paysy_order_transaction_by_user(
                    transaction_id=transaction.id, user=user
                )
            elif purchase_type == "org_subscription":
                TransactionService.accept_org_subscription_transaction(
                    transaction_id=transaction.id
                )
            elif purchase_type == "user_app":
                TransactionService.accept_user_app_transaction(
                    transaction_id=transaction.id
                )
            elif purchase_type == "deal":
                TransactionService.complete_paysy_transaction_online(
                    transaction_id=transaction.id
                )
            elif purchase_type == "assistant":
                print(f"[CryptoCloud] Activating assistant subscription for transaction_id={transaction.id}")
                TransactionService.accept_assistant_transaction(
                    transaction_id=transaction.id
                )
                print(f"[CryptoCloud] Assistant subscription activated successfully")

            else:
                TransactionService.accept_paysy_booking_transaction_by_user(
                    transaction_id=transaction.id, user=user, request=self.request
                )

            response_data = {"message": "Postback received"}
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "Received an unknown status"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LibersaveWebhookView(APIView):
    """
    Webhook handler для Libersave.
    Обрабатывает callback после успешной/неуспешной оплаты.
    """

    def post(self, request, *args, **kwargs):
        payload = request.data
        order_id = payload.get("order_id")
        status_value = payload.get("status")

        if not order_id:
            return Response(
                {"error": "Missing order_id"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parts = order_id.split("|")
            if len(parts) != 3:
                return Response(
                    {"error": "Invalid order_id format"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user_id, transaction_id, purchase_type = parts
            user_id = int(user_id)
            transaction_id = int(transaction_id)
        except (ValueError, AttributeError) as e:
            return Response(
                {"error": f"Error parsing order_id: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = UserService.get(id=user_id)
        transaction = TransactionService.get(id=transaction_id)

        # Libersave может возвращать разные статусы: "success", "completed", "paid" и т.д.
        # Проверяем на успешные статусы
        if status_value in ("success", "completed", "paid"):
            if purchase_type == "product":
                TransactionService.accept_paysy_order_transaction_by_user(
                    transaction_id=transaction.id, user=user
                )
            elif purchase_type == "org_subscription":
                TransactionService.accept_org_subscription_transaction(
                    transaction_id=transaction.id
                )
            elif purchase_type == "user_app":
                TransactionService.accept_user_app_transaction(
                    transaction_id=transaction.id
                )
            elif purchase_type == "deal":
                TransactionService.complete_paysy_transaction_online(
                    transaction_id=transaction.id
                )
            elif purchase_type == "assistant":
                TransactionService.accept_assistant_transaction(
                    transaction_id=transaction.id
                )
            else:
                TransactionService.accept_paysy_booking_transaction_by_user(
                    transaction_id=transaction.id, user=user, request=self.request
                )

            return Response(
                {"message": "Payment processed successfully"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {"message": f"Received status: {status_value}"},
                status=status.HTTP_200_OK,
            )


class BetaPayPaymentTestView(APIView):
    def post(self, request, *args, **kwargs):
        payload = request.data
        merchant_id = payload.get("merchant_id")
        terminal_id = payload.get("terminal_id")
        transaction_id = payload.get("transaction_id")
        case = payload.get("case")

        url = "https://api.betapay.online/api/v3/openbanking-payment-test"
        data = {
            "merchant_id": merchant_id,
            "terminal_id": terminal_id,
            "transaction_id": transaction_id,
            "case": case,
        }
        headers = {"token": BETAPAY_API_TOKEN}
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()

        return Response(response_json)


class MaalyPayResultView(APIView):
    authentication_classes = []
    permission_classes = []

    def _process_successful_payment(self, transaction, user):
        """Обрабатывает успешную оплату в зависимости от типа покупки"""
        payment_info = transaction.payment_info or {}
        purchase_type = payment_info.get("purchase_type", "deal")

        if purchase_type == "product":
            TransactionService.accept_paysy_order_transaction_by_user(
                transaction_id=transaction.id, user=user
            )
        elif purchase_type == "org_subscription":
            TransactionService.accept_org_subscription_transaction(
                transaction_id=transaction.id
            )
        elif purchase_type == "user_app":
            TransactionService.accept_user_app_transaction(
                transaction_id=transaction.id
            )
        elif purchase_type == "deal":
            TransactionService.complete_paysy_transaction_online(
                transaction_id=transaction.id
            )
        elif purchase_type == "assistant":
            TransactionService.accept_assistant_transaction(
                transaction_id=transaction.id
            )
        elif purchase_type == "rent":
            TransactionService.accept_paysy_booking_transaction_by_user(
                transaction_id=transaction.id, user=user, request=None
            )
        else:
            transaction.is_processed = True
            transaction.payment_status = Transaction.ACCEPTED
            transaction.save(update_fields=["is_processed", "payment_status", "updated_at"])

    def get(self, request, *args, **kwargs):
        """GET callback - редирект пользователя после оплаты на MaalyPay"""
        from django.shortcuts import redirect

        from organizations.services.maalypay_service import MaalyPayService

        tx_id = request.GET.get("tx")

        default_success = "https://apofiz.com/payment-success"
        default_failure = "https://apofiz.com/payment-failure"

        if not tx_id:
            return redirect(default_failure)

        transaction = Transaction.objects.select_related("organization", "client").filter(id=tx_id).first()
        if not transaction:
            return redirect(default_failure)

        payment_info = transaction.payment_info or {}
        success_url = payment_info.get("success_url", default_success)
        failure_url = payment_info.get("failure_url", default_failure)

        if transaction.is_processed:
            return redirect(success_url)

        config = MaalyPayService.get_config(transaction.organization)
        if not config:
            return redirect(failure_url)

        # Берём merchant_tx_id из payment_info (там сохранён при создании платежа)
        merchant_tx_id = payment_info.get("merchant_tx_id")
        if not merchant_tx_id:
            return redirect(failure_url)

        if MaalyPayService.is_paid(config.api_key, merchant_tx_id):
            user = transaction.client
            self._process_successful_payment(transaction, user)
            return redirect(success_url)

        return redirect(failure_url)

    def post(self, request, *args, **kwargs):
        """POST webhook от MaalyPay - обработка callback"""
        from organizations.services.maalypay_service import MaalyPayService

        print(f"MaalyPay callback POST received: {request.data}")

        merchant_tx_id = request.data.get("merchantTxId") or request.data.get("merchant_tx_id")

        if not merchant_tx_id:
            # Если merchant_tx_id нет в данных, пробуем взять из query параметра tx
            tx_id = request.GET.get("tx")
            if tx_id:
                # Ищем транзакцию и берём merchant_tx_id из payment_info
                tx = Transaction.objects.filter(id=tx_id).first()
                if tx and tx.payment_info:
                    merchant_tx_id = tx.payment_info.get("merchant_tx_id")

        if not merchant_tx_id:
            return Response({"status": "ok", "message": "No transaction ID"}, status=200)

        # Парсим transaction_id из формата apofiz-{id} или apofiz-{id}-{timestamp}
        if merchant_tx_id.startswith("apofiz-"):
            parts = merchant_tx_id.split("-")
            if len(parts) >= 2:
                transaction_id = int(parts[1])
            else:
                return Response({"status": "ok", "message": "Invalid merchant_tx_id format"}, status=200)
        else:
            return Response({"status": "ok", "message": "Invalid merchant_tx_id format"}, status=200)

        transaction = Transaction.objects.select_related("organization", "client").filter(id=transaction_id).first()
        if not transaction or transaction.is_processed:
            return Response({"status": "ok", "message": "Already processed or not found"}, status=200)

        config = MaalyPayService.get_config(transaction.organization)
        if not config:
            return Response({"status": "ok", "message": "No config"}, status=200)

        if MaalyPayService.is_paid(config.api_key, merchant_tx_id):
            user = transaction.client
            self._process_successful_payment(transaction, user)
            return Response({"status": "ok", "message": "Payment processed"}, status=200)

        return Response({"status": "ok", "message": "Payment not completed yet"}, status=200)


class ResultURLView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ResultURLSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            pg_order_id = validated_data.get("pg_order_id", 1)
            pg_can_reject = validated_data.get("pg_can_reject", 0)
            pg_result = validated_data.get("pg_result", 0)
            pg_description = validated_data.get("pg_description", "")
            user_id = validated_data.get("user_id")
            purchase_type = validated_data.get("purchase_type")
            user_id = int(user_id)
            user = UserService.get(id=user_id)

            if pg_result == 0:
                response_data = {
                    "pg_status": "rejected",
                    "pg_description": pg_description,
                    "pg_salt": validated_data.get("pg_salt", ""),
                    "pg_sig": validated_data.get("pg_sig", ""),
                }
            else:
                if purchase_type == "product":
                    TransactionService.accept_freedompay_order_transaction_by_user(
                        transaction_id=pg_order_id, user=user
                    )
                    response_data = {
                        "pg_status": "ok",
                        "pg_description": "Заказ оплачен",
                        "pg_salt": validated_data.get("pg_salt", ""),
                        "pg_sig": validated_data.get("pg_sig", ""),
                    }
                elif purchase_type == "deal":
                    TransactionService.complete_freedompay_transaction_online(
                        transaction_id=pg_order_id
                    )

                    response_data = {
                        "pg_status": "ok",
                        "pg_description": "Заказ оплачен",
                        "pg_salt": validated_data.get("pg_salt", ""),
                        "pg_sig": validated_data.get("pg_sig", ""),
                    }
                elif purchase_type == "assistant":
                    TransactionService.accept_assistant_transaction(
                        transaction_id=pg_order_id
                    )

                    response_data = {
                        "pg_status": "ok",
                        "pg_description": "Заказ оплачен",
                        "pg_salt": validated_data.get("pg_salt", ""),
                        "pg_sig": validated_data.get("pg_sig", ""),
                    }
                else:
                    TransactionService.accept_freedompay_booking_transaction_by_user(
                        transaction_id=pg_order_id, user=user, request=self.request
                    )
                    response_data = {
                        "pg_status": "ok",
                        "pg_description": "Заказ оплачен",
                        "pg_salt": validated_data.get("pg_salt", ""),
                        "pg_sig": validated_data.get("pg_sig", ""),
                    }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PaymentSuccessView(APIView):
    def post(self, request):
        serializer = PaymentSuccessSerializer(data=request.data)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            pg_order_id = validated_data.get("pg_order_id")
            pg_payment_id = validated_data.get("pg_payment_id")
            pg_error_code = validated_data.get("pg_error_code")
            pg_error_description = validated_data.get("pg_error_description")

            return Response({"message": "Payment successful", **validated_data})


class TransactionWithdrawalView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithdrawalSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        payout_system = serializer.validated_data["payout_system"]
        balance = serializer.validated_data["balance"]
        image_id = serializer.validated_data.get("image_id", None)
        owner_name = serializer.validated_data["owner_name"]
        card_number = serializer.validated_data["card_number"]
        transfer_amount = serializer.validated_data["transfer_amount"]
        utc_offset_minutes = serializer.validated_data.get("utc_offset_minutes")

        recipient = RecipientService.create_recipient(
            payout_system=payout_system,
            image_id=image_id,
            owner_name=owner_name,
            card_number=card_number,
            transfer_amount=transfer_amount,
        )

        transaction = TransactionService.create_withdrawal_transaction(
            request=request,
            organization=organization,
            recipient=recipient,
            balance=balance,
            processed_by=request.user,
            utc_offset_minutes=utc_offset_minutes,
        )

        transaction_serializer = TransactionWithdrawalDetailSerializer(
            transaction, context={"request": request}
        )
        return Response(transaction_serializer.data, status=status.HTTP_201_CREATED)


class TransactionWithdrawalSwiftView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TransactionWithdrawalSwiftSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        organization = serializer.validated_data["organization"]
        balance = serializer.validated_data["balance"]
        image_id = serializer.validated_data.get("image_id", None)
        owner_name = serializer.validated_data["owner_name"]
        swift_bic_code = serializer.validated_data["swift_bic_code"]
        iban_account_number = serializer.validated_data["iban_account_number"]
        country = serializer.validated_data["country"]
        city = serializer.validated_data["city"]
        address = serializer.validated_data["address"]
        postcode = serializer.validated_data["postcode"]
        email = serializer.validated_data["email"]
        transfer_amount = serializer.validated_data["transfer_amount"]
        utc_offset_minutes = serializer.validated_data.get("utc_offset_minutes")

        recipient = RecipientService.create_swift_recipient(
            image_id=image_id,
            owner_name=owner_name,
            swift_bic_code=swift_bic_code,
            iban_account_number=iban_account_number,
            country=country,
            city=city,
            address=address,
            postcode=postcode,
            email=email,
            transfer_amount=transfer_amount,
        )

        transaction = TransactionService.create_withdrawal_swift_transaction(
            request=request,
            organization=organization,
            recipient=recipient,
            balance=balance,
            processed_by=request.user,
            utc_offset_minutes=utc_offset_minutes,
        )

        transaction_serializer = TransactionWithdrawalDetailSerializer(
            transaction, context={"request": request}
        )
        return Response(transaction_serializer.data, status=status.HTTP_201_CREATED)


class PaymentSystemMethodListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PaymentSystemMethodSerializer

    def get_queryset(self):
        return PaymentSystemMethodService.filter(is_active=True)
