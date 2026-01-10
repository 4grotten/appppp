import logging

from django.shortcuts import redirect
from rest_framework.response import Response
from rest_framework.views import APIView

from organizations.services.zinapay_service import ZinaPayService
from transactions.models import Transaction
from transactions.services.transaction_services import TransactionService

logger = logging.getLogger(__name__)

class ZinaPayWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def _process_successful_payment(self, transaction, user):
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
            if not transaction.is_processed:
                transaction.is_processed = True
                transaction.payment_status = Transaction.ACCEPTED
                transaction.save(update_fields=["is_processed", "payment_status", "updated_at"])

    def post(self, request, *args, **kwargs):
        ip = ZinaPayService.get_client_ip(request)
        if ip not in ZinaPayService.ALLOWED_IPS:
             return Response(status=200) # Silent ignore

        data = request.data.get("data", request.data)
        payment_intent_id = data.get("id")
        status_val = data.get("status")

        if not payment_intent_id:
             return Response(status=200)

        transaction = Transaction.objects.filter(
            payment_info__zinapay_payment_intent_id=payment_intent_id
        ).first()

        if not transaction or transaction.is_processed:
             return Response(status=200)


        if status_val == ZinaPayService.STATUS_COMPLETED:
             self._process_successful_payment(transaction, transaction.client)
        elif status_val == ZinaPayService.STATUS_FAILED:
             transaction.payment_status = Transaction.REJECTED
             transaction.save()

        return Response(status=200)

    def get(self, request, *args, **kwargs):
        """Callback: User Redirect."""
        tx_id = request.GET.get("tx")

        success_url = "https://apofiz.com/payment-success"
        failure_url = "https://apofiz.com/payment-failure"

        transaction = None
        if tx_id:
            transaction = Transaction.objects.filter(id=tx_id).first()

        if not transaction:
            return redirect(failure_url)

        payment_info = transaction.payment_info or {}
        success_url = payment_info.get("success_url", success_url)
        failure_url = payment_info.get("failure_url", failure_url)

        if transaction.is_processed:
            return redirect(success_url)

        config = ZinaPayService.get_config(transaction.organization)
        if config:
            p_id = payment_info.get("zinapay_payment_intent_id")
            if p_id and ZinaPayService.is_completed(config.api_token, p_id):
                self._process_successful_payment(transaction, transaction.client)
                return redirect(success_url)

        return redirect(failure_url)
