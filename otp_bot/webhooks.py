"""Webhook handlers for EasyCard events.

Receives transaction notifications from EasyCard Supabase and sends
WhatsApp notifications to users via OTP Bot.
"""

import hashlib
import hmac
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from easycard_integration.services import EasyCardDataService
from .services.otp_service import OTPService

logger = logging.getLogger(__name__)


class EasyCardTransactionWebhookView(APIView):
    """Receive transaction notifications from EasyCard Supabase.

    EasyCard triggers this webhook via an Edge Function when a transaction
    is created or updated. The webhook verifies the HMAC signature, looks
    up the user's phone number, and sends a WhatsApp notification.

    Expected payload:
    {
        "user_id": "uuid",
        "transaction_id": "uuid",
        "type": "top_up|card_payment|transfer_out|...",
        "amount": 100.00,
        "currency": "AED",
        "merchant_name": "Optional merchant",
        "balance_after": 500.00,
        "created_at": "2024-01-15T12:00:00Z"
    }

    Required header:
        X-EasyCard-Signature: HMAC-SHA256 signature of the request body
    """

    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("[WEBHOOK] EasyCard transaction webhook received")

        # 1. Verify webhook signature
        signature = request.headers.get("X-EasyCard-Signature")
        if not self._verify_signature(request.body, signature):
            logger.warning("[WEBHOOK] Invalid signature")
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 2. Parse transaction data
        data = request.data
        user_id = data.get("user_id")
        transaction_id = data.get("transaction_id")
        tx_type = data.get("type")
        amount = data.get("amount")
        currency = data.get("currency", "AED")
        merchant = data.get("merchant_name")
        balance_after = data.get("balance_after")

        if not user_id or not tx_type or amount is None:
            logger.warning("[WEBHOOK] Missing required fields")
            return Response(
                {"error": "Missing required fields: user_id, type, amount"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(
            f"[WEBHOOK] Transaction: user={user_id[:8]}..., "
            f"type={tx_type}, amount={amount} {currency}"
        )

        # 3. Get user phone from EasyCard
        # Try by UUID first (user_id from Supabase), then by apofiz_user_id
        profile = EasyCardDataService.get_profile_by_user_id(user_id)

        # If not found and user_id looks like an integer, try as apofiz_user_id
        if not profile:
            try:
                apofiz_id = int(user_id)
                profile = EasyCardDataService.get_profile_by_apofiz_id(apofiz_id)
            except (ValueError, TypeError):
                pass

        if not profile or not profile.phone:
            logger.warning(f"[WEBHOOK] No phone for user {user_id[:8] if len(user_id) > 8 else user_id}...")
            return Response(
                {"status": "skipped", "reason": "no_phone"},
                status=status.HTTP_200_OK,
            )

        # 4. Check for duplicate notification (idempotency)
        # Use transaction_id to prevent duplicate sends
        cache_key = f"tx_notification_{transaction_id}"
        from django.core.cache import cache
        if cache.get(cache_key):
            logger.info(f"[WEBHOOK] Duplicate notification skipped: {transaction_id}")
            return Response(
                {"status": "skipped", "reason": "duplicate"},
                status=status.HTTP_200_OK,
            )

        # 5. Send WhatsApp notification
        service = OTPService()
        try:
            sent = service.send_transaction_notification(
                phone_number=profile.phone,
                tx_type=tx_type,
                amount=float(amount),
                currency=currency,
                merchant=merchant,
                balance_after=float(balance_after) if balance_after else None,
            )

            if sent:
                # Mark as sent for idempotency (cache for 1 hour)
                cache.set(cache_key, True, timeout=3600)
                logger.info(f"[WEBHOOK] Notification sent for transaction {transaction_id}")
                return Response({"status": "sent"})
            else:
                logger.warning(f"[WEBHOOK] Failed to send notification for {transaction_id}")
                return Response(
                    {"status": "failed", "reason": "send_failed"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except Exception as e:
            logger.error(f"[WEBHOOK] Error sending notification: {e}", exc_info=True)
            return Response(
                {"status": "error", "reason": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature of the webhook payload.

        Args:
            payload: Raw request body bytes
            signature: Signature from X-EasyCard-Signature header

        Returns:
            True if signature is valid
        """
        if not signature:
            return False

        secret = getattr(settings, "EASYCARD_WEBHOOK_SECRET", "")
        if not secret:
            logger.error("[WEBHOOK] EASYCARD_WEBHOOK_SECRET not configured")
            return False

        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)


class EasyCardUserWebhookView(APIView):
    """Receive user creation/update notifications from EasyCard.

    Called when a new user is created or profile is updated in EasyCard.
    Updates the UserEasyCardMapping for user synchronization.

    Expected payload:
    {
        "event": "user.created|user.updated",
        "user_id": "uuid",
        "phone": "+971501234567",
        "first_name": "John",
        "last_name": "Doe"
    }
    """

    permission_classes = [AllowAny]

    def post(self, request):
        logger.info("[WEBHOOK] EasyCard user webhook received")

        # Verify signature
        signature = request.headers.get("X-EasyCard-Signature")
        if not self._verify_signature(request.body, signature):
            logger.warning("[WEBHOOK] Invalid signature")
            return Response(
                {"error": "Invalid signature"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = request.data
        event = data.get("event")
        user_id = data.get("user_id")
        phone = data.get("phone")

        if not user_id or not phone:
            return Response(
                {"error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logger.info(f"[WEBHOOK] User event: {event} for user {user_id[:8]}...")

        # Update mapping
        from .models import UserEasyCardMapping
        from users.models import User

        try:
            # Find Apofiz user by phone
            apofiz_user = User.objects.filter(phone_number=phone).first()
            if not apofiz_user:
                # Try alternative phone formats
                alt_phone = phone.lstrip("+")
                apofiz_user = User.objects.filter(phone_number=alt_phone).first()

            if apofiz_user:
                UserEasyCardMapping.objects.update_or_create(
                    apofiz_user=apofiz_user,
                    defaults={
                        "easycard_user_id": user_id,
                        "phone_number": phone,
                    },
                )
                logger.info(
                    f"[WEBHOOK] Linked Apofiz user {apofiz_user.id} "
                    f"with EasyCard {user_id[:8]}..."
                )
                return Response({"status": "linked"})
            else:
                logger.info(f"[WEBHOOK] No Apofiz user found for phone {phone[:7]}***")
                return Response({"status": "skipped", "reason": "no_apofiz_user"})

        except Exception as e:
            logger.error(f"[WEBHOOK] Error processing user webhook: {e}", exc_info=True)
            return Response(
                {"status": "error", "reason": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify HMAC-SHA256 signature."""
        if not signature:
            return False

        secret = getattr(settings, "EASYCARD_WEBHOOK_SECRET", "")
        if not secret:
            logger.error("[WEBHOOK] EASYCARD_WEBHOOK_SECRET not configured")
            return False

        expected = hmac.new(
            secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)
