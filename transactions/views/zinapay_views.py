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

        print(f"[ZinaPay CALLBACK] Processing payment: tx_id={transaction.id}, purchase_type={purchase_type}")
        logger.info(f"[ZinaPay] Processing successful payment tx={transaction.id}, type={purchase_type}")

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

        print(f"[ZinaPay CALLBACK] Payment processed successfully: tx_id={transaction.id}")

    def post(self, request, *args, **kwargs):
        """POST webhook from ZinaPay"""
        ip = ZinaPayService.get_client_ip(request)

        print(f"[ZinaPay WEBHOOK] POST received from IP: {ip}")
        print(f"[ZinaPay WEBHOOK] Request data: {request.data}")
        logger.info(f"[ZinaPay] Webhook POST from {ip}: {request.data}")

        if ip not in ZinaPayService.ALLOWED_IPS:
            print(f"[ZinaPay WEBHOOK] IP {ip} not in allowed list, ignoring")
            return Response(status=200)

        data = request.data.get("data", request.data)
        payment_intent_id = data.get("id")
        status_val = data.get("status")

        print(f"[ZinaPay WEBHOOK] payment_intent_id={payment_intent_id}, status={status_val}")

        if not payment_intent_id:
            print("[ZinaPay WEBHOOK] No payment_intent_id, returning OK")
            return Response(status=200)

        transaction = Transaction.objects.filter(
            payment_info__zinapay_payment_intent_id=payment_intent_id
        ).first()

        if not transaction:
            print(f"[ZinaPay WEBHOOK] Transaction not found for intent {payment_intent_id}")
            return Response(status=200)

        if transaction.is_processed:
            print(f"[ZinaPay WEBHOOK] Transaction {transaction.id} already processed")
            return Response(status=200)

        print(f"[ZinaPay WEBHOOK] Found transaction: id={transaction.id}, status={transaction.status}, is_processed={transaction.is_processed}")

        if status_val == ZinaPayService.STATUS_COMPLETED:
            print("[ZinaPay WEBHOOK] Status COMPLETED, processing payment")
            self._process_successful_payment(transaction, transaction.client)
        elif status_val in [ZinaPayService.STATUS_FAILED, ZinaPayService.STATUS_CANCELED]:
            print(f"[ZinaPay WEBHOOK] Status {status_val}, marking as REJECTED")
            transaction.payment_status = Transaction.REJECTED
            transaction.save(update_fields=["payment_status", "updated_at"])

        return Response(status=200)

    def get(self, request, *args, **kwargs):
        """GET callback - User redirect after payment"""
        tx_id = request.GET.get("tx")

        print(f"[ZinaPay REDIRECT] GET request: tx_id={tx_id}")
        print(f"[ZinaPay REDIRECT] Full URL: {request.build_absolute_uri()}")
        logger.info(f"[ZinaPay] Redirect callback for tx={tx_id}")

        success_url = "https://apofiz.com/payment-success"
        failure_url = "https://apofiz.com/payment-failure"

        if not tx_id:
            print(f"[ZinaPay REDIRECT] No tx_id, redirecting to failure: {failure_url}")
            return redirect(failure_url)

        transaction = Transaction.objects.select_related("organization", "client").filter(id=tx_id).first()

        if not transaction:
            print(f"[ZinaPay REDIRECT] Transaction {tx_id} not found, redirecting to failure")
            return redirect(failure_url)

        payment_info = transaction.payment_info or {}
        success_url = payment_info.get("success_url", success_url)
        failure_url = payment_info.get("failure_url", failure_url)

        print(f"[ZinaPay REDIRECT] Transaction found: id={transaction.id}, is_processed={transaction.is_processed}")
        print(f"[ZinaPay REDIRECT] payment_info: {payment_info}")
        print(f"[ZinaPay REDIRECT] success_url={success_url}, failure_url={failure_url}")

        if transaction.is_processed:
            print(f"[ZinaPay REDIRECT] Already processed, redirecting to success: {success_url}")
            return redirect(success_url)

        config = ZinaPayService.get_config(transaction.organization)
        if not config:
            print(f"[ZinaPay REDIRECT] No config for org {transaction.organization.id}, redirecting to failure")
            return redirect(failure_url)

        p_id = payment_info.get("zinapay_payment_intent_id")
        print(f"[ZinaPay REDIRECT] Checking payment status for intent: {p_id}")

        if p_id:
            payment_data = ZinaPayService.get_payment_intent(config.api_token, p_id)
            print(f"[ZinaPay REDIRECT] ZinaPay API response: {payment_data}")

            if payment_data and payment_data.get("status") == ZinaPayService.STATUS_COMPLETED:
                print("[ZinaPay REDIRECT] Payment COMPLETED, processing...")
                self._process_successful_payment(transaction, transaction.client)
                print(f"[ZinaPay REDIRECT] Redirecting to success: {success_url}")
                return redirect(success_url)

        print(f"[ZinaPay REDIRECT] Payment not completed, redirecting to failure: {failure_url}")
        return redirect(failure_url)
