import logging

from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.models import Currency
from organizations.models import Organization
from organizations.services.zinapay_service import ZinaPayService
from transactions.models import Transaction
from transactions.serializers.transaction_serializers import (
    ZinaPayPOSCreateSerializer,
    ZinaPayPreprocessSerializer,
    ZinaPayTransactionStatusSerializer,
)
from transactions.services.transaction_services import TransactionService

logger = logging.getLogger(__name__)


class ZinaPayWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def _get_client_ip(self, request) -> str:
        return ZinaPayService.get_client_ip(request)

    def _process_successful_payment(self, transaction, user):
        payment_info = transaction.payment_info or {}
        purchase_type = payment_info.get("purchase_type", "deal")

        logger.info(
            "[ZinaPay] Processing successful payment",
            extra={
                "transaction_id": transaction.id,
                "purchase_type": purchase_type,
            }
        )

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

        logger.info(
            "[ZinaPay] Payment processed successfully",
            extra={
                "transaction_id": transaction.id,
                "purchase_type": purchase_type,
            }
        )

    def post(self, request, *args, **kwargs):
        raw_body = request._request.body

        print(f"\n{'='*60}")
        print("[ZinaPay DEBUG] === WEBHOOK POST RECEIVED ===")
        print(f"[ZinaPay DEBUG] request.data: {request.data}")

        client_ip = self._get_client_ip(request)
        print(f"[ZinaPay DEBUG] client_ip: {client_ip}")
        print(f"[ZinaPay DEBUG] allowed IPs: {ZinaPayService.ALLOWED_IPS}")

        if not ZinaPayService.is_allowed_ip(client_ip):
            print("[ZinaPay DEBUG] WARNING: IP not whitelisted!")
            return Response({"status": "ok", "message": "IP not whitelisted"}, status=200)

        print("[ZinaPay DEBUG] IP check: OK")

        event = request.data.get("event")
        data = request.data.get("data", {})

        if not data and "id" in request.data:
            data = request.data

        payment_intent_id = data.get("id")
        zinapay_status = data.get("status")

        print(f"[ZinaPay DEBUG] event: {event}")
        print(f"[ZinaPay DEBUG] payment_intent_id: {payment_intent_id}")
        print(f"[ZinaPay DEBUG] status: {zinapay_status}")

        if event and event != "payment_intent.status.updated":
            print(f"[ZinaPay DEBUG] Ignoring event: {event}")
            return Response({"status": "ok", "message": "Event ignored"})

        if not payment_intent_id:
            print("[ZinaPay DEBUG] ERROR: Missing payment_intent_id!")
            return Response({"status": "ok", "message": "No payment intent ID"})

        transaction = Transaction.objects.filter(
            payment_info__zinapay_payment_intent_id=payment_intent_id,
        ).select_related("organization", "client").first()

        print(f"[ZinaPay DEBUG] transaction found: {transaction is not None}")
        if transaction:
            print(f"[ZinaPay DEBUG] transaction_id: {transaction.id}")
            print(f"[ZinaPay DEBUG] is_processed: {transaction.is_processed}")

        if not transaction:
            print(f"[ZinaPay DEBUG] ERROR: Transaction not found for payment_intent_id={payment_intent_id}")
            return Response({"status": "ok", "message": "Transaction not found"})

        if transaction.is_processed:
            print("[ZinaPay DEBUG] Transaction already processed, skipping")
            return Response({"status": "ok", "message": "Already processed"})

        config = ZinaPayService.get_config(transaction.organization)
        if not config:
            print(f"[ZinaPay DEBUG] ERROR: No ZinaPay config for org_id={transaction.organization_id}")
            return Response({"status": "ok", "message": "Config not found"})

        if config.webhook_secret:
            signature = request.headers.get("X-Hmac-Signature", "")
            print("[ZinaPay DEBUG] Verifying HMAC signature...")
            if not ZinaPayService.verify_webhook_signature(
                raw_body,
                signature,
                config.webhook_secret
            ):
                print("[ZinaPay DEBUG] ERROR: Invalid HMAC signature!")
                return Response({"status": "ok", "message": "Signature verification failed"})
            print("[ZinaPay DEBUG] HMAC signature: OK")

        print(f"[ZinaPay DEBUG] Processing status: {zinapay_status}")

        if zinapay_status == ZinaPayService.STATUS_COMPLETED:
            print("[ZinaPay DEBUG] Status is COMPLETED, verifying with API...")
            if not ZinaPayService.is_completed(config.api_token, payment_intent_id):
                print("[ZinaPay DEBUG] ERROR: API status verification failed!")
                logger.error(
                    "[ZinaPay] Status mismatch - API says not completed",
                    extra={
                        "transaction_id": transaction.id,
                        "payment_intent_id": payment_intent_id,
                        "webhook_status": zinapay_status,
                    }
                )
                return Response({"status": "ok", "message": "Status verification failed"})

            print("[ZinaPay DEBUG] API verification: OK, processing payment...")
            self._process_successful_payment(transaction, transaction.client)
            print("[ZinaPay DEBUG] Payment processed successfully!")

            logger.info(
                "[ZinaPay] Webhook processed successfully",
                extra={
                    "transaction_id": transaction.id,
                    "status": zinapay_status,
                }
            )

        elif zinapay_status == ZinaPayService.STATUS_FAILED:
            print(f"[ZinaPay DEBUG] Status is FAILED, error: {data.get('latest_error')}")
            logger.info(
                "[ZinaPay] Payment failed",
                extra={
                    "transaction_id": transaction.id,
                    "payment_intent_id": payment_intent_id,
                    "error": data.get("latest_error"),
                }
            )
            transaction.payment_status = Transaction.REJECTED
            transaction.save(update_fields=["payment_status", "updated_at"])
            print("[ZinaPay DEBUG] Transaction marked as REJECTED")

        elif zinapay_status == ZinaPayService.STATUS_CANCELED:
            print("[ZinaPay DEBUG] Status is CANCELED")
            logger.info(
                "[ZinaPay] Payment cancelled",
                extra={
                    "transaction_id": transaction.id,
                    "payment_intent_id": payment_intent_id,
                }
            )

        print("[ZinaPay DEBUG] === WEBHOOK POST COMPLETE ===")
        print(f"{'='*60}\n")
        return Response({"status": "ok"})

    def get(self, request, *args, **kwargs):
        print(f"\n{'='*60}")
        print("[ZinaPay DEBUG] === GET CALLBACK RECEIVED ===")
        print(f"[ZinaPay DEBUG] Full URL: {request.build_absolute_uri()}")
        print(f"[ZinaPay DEBUG] Query params: {dict(request.GET)}")

        payment_intent_id = request.GET.get("payment_intent_id") or request.GET.get("id")
        tx_id = request.GET.get("tx")

        print(f"[ZinaPay DEBUG] payment_intent_id: {payment_intent_id}")
        print(f"[ZinaPay DEBUG] tx_id: {tx_id}")

        default_success = "https://apofiz.com/payment-success"
        default_failure = "https://apofiz.com/payment-failure"

        logger.info(
            "[ZinaPay] GET redirect received",
            extra={
                "payment_intent_id": payment_intent_id,
                "tx_id": tx_id,
            }
        )

        transaction = None

        if tx_id:
            transaction = Transaction.objects.filter(id=tx_id).select_related(
                "organization", "client"
            ).first()
            print(f"[ZinaPay DEBUG] Searched by tx_id, found: {transaction is not None}")
        elif payment_intent_id:
            transaction = Transaction.objects.filter(
                payment_info__zinapay_payment_intent_id=payment_intent_id
            ).select_related("organization", "client").first()
            print(f"[ZinaPay DEBUG] Searched by payment_intent_id, found: {transaction is not None}")

        if not transaction:
            print("[ZinaPay DEBUG] ERROR: Transaction not found! Redirecting to failure")
            logger.warning(
                "[ZinaPay] Transaction not found on GET redirect",
                extra={"payment_intent_id": payment_intent_id, "tx_id": tx_id}
            )
            return redirect(default_failure)

        print(f"[ZinaPay DEBUG] Transaction found: id={transaction.id}")
        print(f"[ZinaPay DEBUG] is_processed: {transaction.is_processed}")
        print(f"[ZinaPay DEBUG] payment_status: {transaction.payment_status}")

        payment_info = transaction.payment_info or {}
        success_url = payment_info.get("success_url", default_success)
        failure_url = payment_info.get("failure_url", default_failure)

        print(f"[ZinaPay DEBUG] success_url: {success_url}")
        print(f"[ZinaPay DEBUG] failure_url: {failure_url}")

        if transaction.is_processed:
            print("[ZinaPay DEBUG] Already processed, redirecting to success")
            return redirect(success_url)

        config = ZinaPayService.get_config(transaction.organization)
        if not config:
            print("[ZinaPay DEBUG] ERROR: No ZinaPay config for org! Redirecting to failure")
            return redirect(failure_url)

        if not payment_intent_id:
            payment_intent_id = payment_info.get("zinapay_payment_intent_id")
            print(f"[ZinaPay DEBUG] Got payment_intent_id from payment_info: {payment_intent_id}")

        if not payment_intent_id:
            print("[ZinaPay DEBUG] ERROR: No payment_intent_id! Redirecting to failure")
            return redirect(failure_url)

        print("[ZinaPay DEBUG] Checking payment status with ZinaPay API...")
        if ZinaPayService.is_completed(config.api_token, payment_intent_id):
            print("[ZinaPay DEBUG] API says COMPLETED, processing payment...")
            self._process_successful_payment(transaction, transaction.client)
            print("[ZinaPay DEBUG] Payment processed! Redirecting to success")
            print(f"{'='*60}\n")
            return redirect(success_url)

        print("[ZinaPay DEBUG] Payment not completed, redirecting to failure")
        print(f"{'='*60}\n")
        return redirect(failure_url)

class ZinaPayPOSCreateView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ZinaPayPOSCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        amount = data['amount']
        currency_code = data['currency']
        organization_id = data['organization_id']
        note = data.get('note', '')
        generate_qr = data.get('generate_qr', True)

        try:
            organization = Organization.objects.get(id=organization_id)
        except Organization.DoesNotExist:
            return Response(
                {"error": _("Organization not found")},
                status=status.HTTP_404_NOT_FOUND
            )

        config = ZinaPayService.get_config(organization)
        if not config:
            return Response(
                {"error": _("ZinaPay is not configured for this organization")},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            currency = Currency.objects.get(code=currency_code)
        except Currency.DoesNotExist:
            return Response(
                {"error": _(f"Currency {currency_code} not found")},
                status=status.HTTP_400_BAD_REQUEST
            )

        transaction = Transaction.objects.create(
            organization=organization,
            client=request.user,
            currency=currency,
            original_amount=amount,
            type=Transaction.ONLINE,
            status=Transaction.ACCEPTED,
            payment_status=Transaction.IN_PROGRESS,
            is_processed=False,
            payment_info={
                "payment_mode": ZinaPayService.MODE_POS,
                "purchase_type": "pos_payment",
                "user_id": request.user.id,
                "note": note,
            }
        )

        logger.info(
            "[ZinaPay POS] Transaction created",
            extra={
                "transaction_id": transaction.id,
                "amount": amount,
                "currency": currency_code,
                "org_id": organization_id,
            }
        )

        amount_fils = ZinaPayService.convert_to_fils(amount, currency_code)

        base_url = request.build_absolute_uri('/').rstrip('/')
        success_url = f"{base_url}/api/v1/transactions/zinapay/callback/?tx={transaction.id}"
        failure_url = f"{base_url}/api/v1/transactions/zinapay/callback/?tx={transaction.id}"

        org_title = organization.title or "Payment"
        message = f"{org_title} • {note}".strip(" •") if note else org_title

        result = ZinaPayService.create_payment_intent(
            api_token=config.api_token,
            amount=amount_fils,
            currency_code=currency_code,
            success_url=success_url,
            cancel_url=failure_url,
            failure_url=failure_url,
            message=message,
        )

        if not result:
            transaction.delete()
            return Response(
                {"error": _("Failed to create ZinaPay payment. Please try again.")},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if transaction.payment_info is None:
            transaction.payment_info = type(transaction.payment_info)()
        transaction.payment_info.update({
            "zinapay_payment_intent_id": result["id"],
            "success_url": success_url,
            "failure_url": failure_url,
        })
        transaction.save(update_fields=["payment_info"])

        logger.info(
            "[ZinaPay POS] Payment intent created",
            extra={
                "transaction_id": transaction.id,
                "payment_intent_id": result["id"],
                "redirect_url": result["redirect_url"],
            }
        )

        qr_code_base64 = None
        if generate_qr:
            redirect_url = result.get("redirect_url")
            if redirect_url is not None:
                qr_code_base64 = ZinaPayService.generate_qr_code(redirect_url)
                if not qr_code_base64:
                    logger.warning(
                        "[ZinaPay POS] QR code generation failed",
                        extra={"transaction_id": transaction.id}
                    )
            else:
                logger.warning(
                    "[ZinaPay POS] No redirect_url provided for QR code generation",
                    extra={"transaction_id": transaction.id}
                )

        response_data = {
            "transaction_id": transaction.id,
            "redirect_url": result["redirect_url"],
            "qr_code_base64": qr_code_base64,
            "amount": str(amount),
            "currency": currency_code,
            "payment_mode": ZinaPayService.MODE_POS,
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class ZinaPayTransactionStatusView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ZinaPayTransactionStatusSerializer

    def get(self, request, *args, **kwargs):
        transaction_id = request.query_params.get('transaction_id')

        if not transaction_id:
            return Response(
                {"error": _("transaction_id is required")},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            transaction = Transaction.objects.get(
                id=transaction_id,
                client=request.user
            )
        except Transaction.DoesNotExist:
            return Response(
                {"error": _("Transaction not found")},
                status=status.HTTP_404_NOT_FOUND
            )

        payment_info = transaction.payment_info or {}
        payment_mode = payment_info.get("payment_mode", ZinaPayService.MODE_P2P)

        response_data = {
            "transaction_id": transaction.id,
            "is_processed": transaction.is_processed,
            "payment_status": transaction.payment_status,
            "status": transaction.status,
            "amount": str(transaction.original_amount),
            "currency": transaction.currency.code,
            "payment_mode": payment_mode,
        }

        return Response(response_data, status=status.HTTP_200_OK)


class ZinaPayPreprocessView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ZinaPayPreprocessSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )


        organization = serializer.validated_data["organization"]
        client = serializer.validated_data.get("client") or request.user
        cart = serializer.validated_data.get("cart", None)
        order_comment = serializer.validated_data.get("order_comment", None)
        currency_code = serializer.validated_data["currency"]
        amount = serializer.validated_data["amount"]

        from common.models import Currency
        try:
            currency = Currency.objects.get(code=currency_code)
        except Currency.DoesNotExist:
            return Response(
                data={"error": _(f"Currency {currency_code} not found in system")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from transactions.services.transaction_services import TransactionService

        new_transaction = TransactionService.preprocess_transaction(
            client=client,
            organization=organization,
            cart=cart,
            processed_by=request.user,
            order_comment=order_comment,
        )

        new_transaction.currency = currency
        new_transaction.status = Transaction.ACCEPTED
        new_transaction.original_amount = amount
        new_transaction.save(update_fields=["currency", "status", "original_amount"])

        logger.info(
            "[ZinaPay] Transaction preprocessed",
            extra={
                "transaction_id": new_transaction.id,
                "organization_id": organization.id,
                "client_id": client.id,
                "currency": currency_code,
                "has_cart": cart is not None,
            }
        )

        data = {
            "transaction_id": new_transaction.id,
            "organization_id": organization.id,
            "client_id": client.id,
            "currency": currency_code,
            "status": new_transaction.status,
            "payment_status": new_transaction.payment_status,
        }

        return Response(data=data, status=status.HTTP_201_CREATED)
