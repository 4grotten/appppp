"""
ZinaPay Payment Service

ZinaPay (Ziina) is a UAE-based payment gateway supporting multiple currencies.
API Documentation: https://docs.ziina.com/

This service handles Direct Merchant Integration:
1. Create Payment Intent -> Get redirect_url
2. Redirect user to payment page
3. Receive webhook notification
4. Verify payment status
"""

import hashlib
import hmac
import json
import logging
import time
import uuid
from decimal import Decimal
from typing import Optional, TypedDict

import requests
from django.db import IntegrityError, transaction as db_transaction
from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException

logger = logging.getLogger(__name__)


class PaymentIntentResponse(TypedDict):
    """Response from create payment intent."""
    id: str
    account_id: str
    amount: int
    tip_amount: int
    currency_code: str
    created_at: str
    status: str
    operation_id: str
    redirect_url: Optional[str]
    success_url: Optional[str]
    cancel_url: Optional[str]
    message: Optional[str]
    fee_amount: Optional[int]
    allow_tips: bool


class ZinaPayService:
    """
    Service for ZinaPay (Ziina) payment gateway integration.

    Supports two payment modes:
    1. P2P (Peer-to-Peer): User initiates payment through app
    2. POS (Point of Sale): Merchant generates QR code for customer to scan

    Features:
    - Payment Intent creation
    - Payment status verification
    - Webhook signature verification (HMAC SHA-256)
    - IP whitelist validation
    - QR code generation for POS terminals
    """

    BASE_URL = "https://api-v2.ziina.com/api"
    TIMEOUT = 60
    PAYMENT_SYSTEM_ID = 7

    # Payment modes
    MODE_P2P = "p2p"  # Peer-to-peer: user pays through app
    MODE_POS = "pos"  # Point of Sale: merchant terminal with QR code

    # Official ZinaPay webhook IP addresses
    ALLOWED_IPS = frozenset([
        "3.29.184.186",
        "3.29.190.95",
        "20.233.47.127",
    ])

    # Supported currencies by ZinaPay
    SUPPORTED_CURRENCIES = frozenset([
        "AED", "USD", "EUR", "GBP", "SAR", "QAR", "INR",
        "BHD", "KWD", "OMR",  # Three-decimal currencies
    ])

    # Three-decimal currencies (amount must be rounded to nearest 10)
    THREE_DECIMAL_CURRENCIES = frozenset(["BHD", "KWD", "OMR"])

    # Payment Intent statuses
    STATUS_REQUIRES_PAYMENT = "requires_payment_instrument"
    STATUS_PENDING = "pending"
    STATUS_REQUIRES_ACTION = "requires_user_action"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELED = "canceled"

    # ==================== Configuration Methods ====================

    @classmethod
    def get_config(cls, organization):
        """Get ZinaPay configuration for organization."""
        from organizations.models import ZinaPayOrganizationPaymentSystem
        return ZinaPayOrganizationPaymentSystem.objects.filter(
            organization=organization
        ).first()

    @classmethod
    def is_configured(cls, organization) -> bool:
        """Check if ZinaPay is configured for organization."""
        from organizations.models import ZinaPayOrganizationPaymentSystem
        return ZinaPayOrganizationPaymentSystem.objects.filter(
            organization=organization
        ).exists()

    @classmethod
    def connect_to_organization(
        cls,
        organization,
        api_token: str,
        webhook_secret: Optional[str] = None,
        currencies: Optional[list] = None,
    ) -> dict:
        """
        Connect ZinaPay to organization.

        Args:
            organization: Organization instance
            api_token: Bearer token from ZinaPay dashboard
            webhook_secret: Optional secret for HMAC webhook verification
            currencies: List of currency codes to support

        Returns:
            dict with created configuration
        """
        from organizations.models import ZinaPayOrganizationPaymentSystem

        if not api_token:
            raise BadRequestException(_("api_token is required"))

        try:
            with db_transaction.atomic():
                defaults = {
                    "api_token": api_token,
                }
                if webhook_secret:
                    defaults["webhook_secret"] = webhook_secret

                config, created = ZinaPayOrganizationPaymentSystem.objects.get_or_create(
                    organization=organization,
                    defaults=defaults,
                )

                if not created:
                    raise BadRequestException(_("ZinaPay is already configured for this organization"))

                # Add currencies if specified
                if currencies:
                    from common.models import Currency
                    currency_objects = Currency.objects.filter(code__in=currencies)
                    config.currencies.set(currency_objects)

                # Activate ZinaPay for organization
                organization.zina_pay_activated = True
                organization.zina_pay_confirmed = True
                organization.save(update_fields=["zina_pay_activated", "zina_pay_confirmed"])

                logger.info(
                    "[ZinaPay] Connected to organization",
                    extra={
                        "org_id": organization.id,
                        "org_title": organization.title,
                        "has_webhook_secret": bool(webhook_secret),
                        "currencies": currencies,
                    }
                )

                result = {
                    "api_token": api_token[:20] + "***",  # Masked
                    "created": True,
                }
                if webhook_secret:
                    result["webhook_secret_configured"] = True
                if currencies:
                    result["currencies"] = currencies
                return result

        except IntegrityError as e:
            logger.error(
                "[ZinaPay] IntegrityError during connection",
                extra={"org_id": organization.id, "error": str(e)},
                exc_info=True
            )
            raise BadRequestException(_("ZinaPay is already configured for this organization"))

    @classmethod
    def update_currencies(cls, organization, currencies: list) -> list:
        """Update supported currencies for ZinaPay organization."""
        config = cls.get_config(organization)
        if not config:
            raise BadRequestException(_("ZinaPay is not configured for this organization"))

        from common.models import Currency
        currency_objects = Currency.objects.filter(code__in=currencies)
        config.currencies.set(currency_objects)

        logger.info(
            "[ZinaPay] Updated currencies for organization",
            extra={
                "org_id": organization.id,
                "currencies": currencies,
            }
        )

        return list(config.currencies.values_list('code', flat=True))

    # ==================== Payment Methods ====================

    @classmethod
    def create_payment_intent(
        cls,
        api_token: str,
        amount: int,
        currency_code: str,
        success_url: str,
        cancel_url: str,
        failure_url: Optional[str] = None,
        message: Optional[str] = None,
        test: bool = False,
        allow_tips: bool = False,
        expiry: Optional[str] = None,
    ) -> Optional[PaymentIntentResponse]:
        """
        Create a Payment Intent in ZinaPay.

        Args:
            api_token: Bearer token
            amount: Amount in fils (100 AED = 10000 fils)
            currency_code: ISO-4217 currency code (AED, USD, etc.)
            success_url: Redirect URL on successful payment
            cancel_url: Redirect URL on cancelled payment
            failure_url: Redirect URL on failed payment (optional)
            message: Message displayed on payment page
            test: If True, creates test payment (no real charge)
            allow_tips: If True, allows tips on payment page
            expiry: Unix timestamp in milliseconds for payment expiry

        Returns:
            PaymentIntentResponse with id, redirect_url, status, etc.
            None if creation failed

        Raises:
            BadRequestException: If currency is not supported
        """
        # Validate currency before creating payment intent
        cls.validate_currency(currency_code)

        url = f"{cls.BASE_URL}/payment_intent"

        payload = {
            "amount": amount,
            "currency_code": currency_code,
            "success_url": success_url,
            "cancel_url": cancel_url,
        }

        if failure_url:
            payload["failure_url"] = failure_url
        if message:
            payload["message"] = message
        if test:
            payload["test"] = True
        if allow_tips:
            payload["allow_tips"] = True
        if expiry:
            payload["expiry"] = expiry

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        logger.info(
            "[ZinaPay] Creating payment intent",
            extra={
                "amount": amount,
                "currency_code": currency_code,
                "test_mode": test,
            }
        )

        try:
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=cls.TIMEOUT
            )

            logger.debug(
                "[ZinaPay] API Response",
                extra={
                    "status_code": response.status_code,
                    "response_body": response.text[:500],
                }
            )

            if response.status_code not in (200, 201):
                logger.error(
                    "[ZinaPay] Payment intent creation failed",
                    extra={
                        "status_code": response.status_code,
                        "response": response.text,
                        "amount": amount,
                        "currency": currency_code,
                    }
                )
                return None

            data = response.json()

            if not data.get("redirect_url"):
                logger.error(
                    "[ZinaPay] Missing redirect_url in response",
                    extra={"response_data": data}
                )
                return None

            logger.info(
                "[ZinaPay] Payment intent created successfully",
                extra={
                    "payment_intent_id": data.get("id"),
                    "status": data.get("status"),
                    "amount": amount,
                }
            )

            return data

        except requests.Timeout:
            logger.error(
                "[ZinaPay] Request timeout",
                extra={"timeout": cls.TIMEOUT},
                exc_info=True
            )
            return None
        except requests.RequestException as e:
            logger.error(
                "[ZinaPay] Request failed",
                extra={"error": str(e)},
                exc_info=True
            )
            return None
        except json.JSONDecodeError as e:
            logger.error(
                "[ZinaPay] Invalid JSON response",
                extra={"error": str(e)},
                exc_info=True
            )
            return None

    @classmethod
    def get_payment_intent(
        cls,
        api_token: str,
        payment_intent_id: str
    ) -> Optional[PaymentIntentResponse]:
        """
        Get Payment Intent details from ZinaPay.

        Args:
            api_token: Bearer token
            payment_intent_id: ID of the payment intent

        Returns:
            PaymentIntentResponse with current status
            None if request failed
        """
        url = f"{cls.BASE_URL}/payment_intent/{payment_intent_id}"

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        logger.debug(
            "[ZinaPay] Getting payment intent",
            extra={"payment_intent_id": payment_intent_id}
        )

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=cls.TIMEOUT
            )

            if response.status_code != 200:
                logger.warning(
                    "[ZinaPay] Failed to get payment intent",
                    extra={
                        "status_code": response.status_code,
                        "payment_intent_id": payment_intent_id,
                        "response": response.text[:200],
                    }
                )
                return None

            data = response.json()

            logger.info(
                "[ZinaPay] Payment intent retrieved",
                extra={
                    "payment_intent_id": payment_intent_id,
                    "status": data.get("status"),
                    "amount": data.get("amount"),
                }
            )

            return data

        except requests.Timeout:
            logger.error(
                "[ZinaPay] Get payment intent timeout",
                extra={"payment_intent_id": payment_intent_id},
                exc_info=True
            )
            return None
        except requests.RequestException as e:
            logger.error(
                "[ZinaPay] Get payment intent failed",
                extra={
                    "payment_intent_id": payment_intent_id,
                    "error": str(e),
                },
                exc_info=True
            )
            return None

    @classmethod
    def is_completed(cls, api_token: str, payment_intent_id: str) -> bool:
        """Check if payment intent is completed."""
        data = cls.get_payment_intent(api_token, payment_intent_id)
        if data is None:
            return False
        return data.get("status") == cls.STATUS_COMPLETED

    # ==================== Webhook Methods ====================

    @classmethod
    def register_webhook(
        cls,
        api_token: str,
        url: str,
        secret: Optional[str] = None,
    ) -> bool:
        """
        Register webhook URL in ZinaPay.

        Args:
            api_token: Bearer token
            url: Webhook URL to receive notifications
            secret: Optional HMAC secret for signature verification

        Returns:
            True if registration successful
        """
        endpoint = f"{cls.BASE_URL}/webhook"

        payload = {"url": url}
        if secret:
            payload["secret"] = secret

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        logger.info(
            "[ZinaPay] Registering webhook",
            extra={
                "url": url,
                "has_secret": bool(secret),
            }
        )

        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=cls.TIMEOUT
            )

            if response.status_code != 200:
                logger.error(
                    "[ZinaPay] Webhook registration failed",
                    extra={
                        "status_code": response.status_code,
                        "response": response.text,
                    }
                )
                return False

            data = response.json()
            success = data.get("success", False)

            if success:
                logger.info("[ZinaPay] Webhook registered successfully")
            else:
                logger.error(
                    "[ZinaPay] Webhook registration returned error",
                    extra={"error": data.get("error")}
                )

            return success

        except requests.RequestException as e:
            logger.error(
                "[ZinaPay] Webhook registration request failed",
                extra={"error": str(e)},
                exc_info=True
            )
            return False

    @classmethod
    def verify_webhook_signature(
        cls,
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """
        Verify webhook HMAC signature.

        ZinaPay sends X-Hmac-Signature header with hexadecimal encoded
        SHA-256 HMAC signature of the request body.

        Args:
            payload: Raw request body bytes
            signature: X-Hmac-Signature header value
            secret: Webhook secret configured during registration

        Returns:
            True if signature is valid
        """
        if not signature or not secret:
            return False

        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        is_valid = hmac.compare_digest(signature.lower(), expected_signature.lower())

        if not is_valid:
            logger.warning(
                "[ZinaPay] Invalid webhook signature",
                extra={
                    "received": signature[:20] + "...",
                    "expected": expected_signature[:20] + "...",
                }
            )

        return is_valid

    @classmethod
    def is_allowed_ip(cls, ip_address: str) -> bool:
        """
        Check if IP address is in ZinaPay whitelist.

        Args:
            ip_address: Client IP address

        Returns:
            True if IP is allowed
        """
        return ip_address in cls.ALLOWED_IPS

    # ==================== Utility Methods ====================

    @classmethod
    def validate_currency(cls, currency_code: str) -> None:
        """
        Validate that currency is supported by ZinaPay.

        Args:
            currency_code: ISO-4217 currency code

        Raises:
            BadRequestException: If currency is not supported
        """
        if not currency_code:
            raise BadRequestException(_("Currency code is required"))

        currency_upper = currency_code.upper()

        if currency_upper not in cls.SUPPORTED_CURRENCIES:
            supported_list = ", ".join(sorted(cls.SUPPORTED_CURRENCIES))
            raise BadRequestException(
                _(f"Unsupported currency for ZinaPay: {currency_code}. "
                  f"Supported currencies: {supported_list}")
            )

    @classmethod
    def generate_operation_id(cls, transaction_id: int) -> str:
        """
        Generate unique operation_id for payment intent.

        Format: apofiz-zina-{transaction_id}-{timestamp}
        """
        timestamp = int(time.time())
        return f"apofiz-zina-{transaction_id}-{timestamp}"

    @classmethod
    def convert_to_fils(cls, amount: Decimal, currency_code: str = "AED") -> int:
        """
        Convert decimal amount to fils (base units).

        Standard currencies: 100.50 -> 10050
        Three-decimal currencies (BHD, KWD, OMR): 100.500 -> 100500

        Note: Three-decimal currencies must be rounded to nearest 10.

        Args:
            amount: Decimal amount
            currency_code: Currency code

        Returns:
            Amount in fils/base units
        """
        if currency_code in cls.THREE_DECIMAL_CURRENCIES:
            # Three decimal places: multiply by 1000, round to nearest 10
            fils = int(amount * 1000)
            # Round to nearest 10 as required by ZinaPay
            fils = round(fils / 10) * 10
        else:
            # Standard two decimal places: multiply by 100
            fils = int(amount * 100)

        return fils

    @classmethod
    def convert_from_fils(cls, fils: int, currency_code: str = "AED") -> Decimal:
        """
        Convert fils (base units) to decimal amount.

        Args:
            fils: Amount in fils/base units
            currency_code: Currency code

        Returns:
            Decimal amount
        """
        if currency_code in cls.THREE_DECIMAL_CURRENCIES:
            return Decimal(fils) / Decimal(1000)
        return Decimal(fils) / Decimal(100)

    @classmethod
    def generate_webhook_secret(cls) -> str:
        """Generate a secure random webhook secret."""
        return uuid.uuid4().hex + uuid.uuid4().hex

    @classmethod
    def get_client_ip(cls, request) -> str:
        """
        Extract client IP from Django request.
        Handles X-Forwarded-For header for reverse proxy setups.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain (original client)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    @classmethod
    def generate_qr_code(cls, redirect_url: str, size: int = 300) -> str:
        """
        Generate QR code for payment URL (POS terminal mode).

        Args:
            redirect_url: ZinaPay payment URL to encode
            size: QR code size in pixels (default: 300)

        Returns:
            Base64-encoded PNG image string (data:image/png;base64,...)
        """
        try:
            import qrcode
            from io import BytesIO
            import base64

            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(redirect_url)
            qr.make(fit=True)

            # Generate image
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode()

            logger.debug(
                "[ZinaPay] QR code generated",
                extra={"url_length": len(redirect_url), "size": size}
            )

            return f"data:image/png;base64,{img_base64}"

        except ImportError:
            logger.error(
                "[ZinaPay] qrcode library not installed. Install with: pip install qrcode[pil]",
                exc_info=True
            )
            return ""
        except Exception as e:
            logger.error(
                "[ZinaPay] QR code generation failed",
                extra={"error": str(e)},
                exc_info=True
            )
            return ""
