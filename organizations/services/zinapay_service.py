import hashlib
import hmac
import logging
from decimal import Decimal
from typing import Optional, TypedDict

import requests
from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException

logger = logging.getLogger(__name__)


class PaymentIntentResponse(TypedDict):
    id: str
    account_id: str
    amount: int
    currency_code: str
    status: str
    redirect_url: Optional[str]
    success_url: Optional[str]
    cancel_url: Optional[str]
    message: Optional[str]


class ZinaPayService:
    """
    Service for ZinaPay (Ziina) P2P integration.
    Only Online Payment flow is supported.
    """

    BASE_URL = "https://api-v2.ziina.com/api"
    TIMEOUT = 30
    PAYMENT_SYSTEM_ID = 7

    MODE_P2P = "p2p"

    ALLOWED_IPS = frozenset([
        "3.29.184.186",
        "3.29.190.95",
        "20.233.47.127",
    ])

    SUPPORTED_CURRENCIES = frozenset([
        "AED", "USD", "EUR", "GBP", "SAR", "QAR", "INR",
        "BHD", "KWD", "OMR"
    ])

    THREE_DECIMAL_CURRENCIES = frozenset(["BHD", "KWD", "OMR"])

    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CANCELED = "canceled"

    @classmethod
    def get_config(cls, organization):
        from organizations.models import ZinaPayOrganizationPaymentSystem
        return ZinaPayOrganizationPaymentSystem.objects.filter(
            organization=organization
        ).first()

    @classmethod
    def is_configured(cls, organization) -> bool:
        from organizations.models import ZinaPayOrganizationPaymentSystem
        return ZinaPayOrganizationPaymentSystem.objects.filter(
            organization=organization
        ).exists()

    @classmethod
    def validate_currency(cls, currency_code: str) -> None:
        """Strictly validate currency against supported list."""
        if not currency_code:
            raise BadRequestException(_("Currency code is required"))

        code = currency_code.upper()
        if code not in cls.SUPPORTED_CURRENCIES:
            raise BadRequestException(
                _(f"Currency {code} is not supported by ZinaPay. "
                  f"Supported: {', '.join(sorted(cls.SUPPORTED_CURRENCIES))}")
            )

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
    ) -> Optional[PaymentIntentResponse]:

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

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=cls.TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"[ZinaPay] Create Intent Failed: {e}", exc_info=True)
            return None

    @classmethod
    def get_payment_intent(cls, api_token: str, payment_intent_id: str) -> Optional[dict]:
        """Fetch payment details from ZinaPay API."""
        url = f"{cls.BASE_URL}/payment_intent/{payment_intent_id}"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.get(url, headers=headers, timeout=cls.TIMEOUT)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"[ZinaPay] Get Intent Failed: {e}")
        return None

    @classmethod
    def is_completed(cls, api_token: str, payment_intent_id: str) -> bool:
        data = cls.get_payment_intent(api_token, payment_intent_id)
        if not data:
            return False
        return data.get("status") == cls.STATUS_COMPLETED

    @classmethod
    def convert_to_fils(cls, amount: Decimal, currency_code: str = "AED") -> int:
        """Convert decimal amount to minor units (fils/cents)."""
        if currency_code in cls.THREE_DECIMAL_CURRENCIES:
            fils = int(amount * 1000)
            return round(fils / 10) * 10
        else:
            return int(amount * 100)

    @classmethod
    def get_client_ip(cls, request) -> str:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')

    @classmethod
    def verify_webhook_signature(cls, payload: bytes, signature: str, secret: str) -> bool:
        if not signature or not secret:
            return False
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature.lower(), expected.lower())
