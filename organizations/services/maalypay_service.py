from typing import Optional, TypedDict
import logging
import json

import requests
from django.db import IntegrityError
from django.db import transaction as db_transaction
from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException
from organizations.models import (
    MaalyPayOrganizationPaymentSystem,
    Organization,
)

logger = logging.getLogger(__name__)


class MaalyPayOrderStatus(TypedDict):
    fiatAmount: str
    status: bool
    filledAmount: str
    txHash: Optional[str]
    network: Optional[str]
    asset: Optional[str]
    txLink: Optional[str]


class MaalyPayService:

    BASE_URL = "https://maalyportal.com/api/omerch"
    TIMEOUT = 60
    PAYMENT_SYSTEM_ID = 6

    @classmethod
    def get_config(
        cls, organization: Organization
    ) -> Optional[MaalyPayOrganizationPaymentSystem]:
        return MaalyPayOrganizationPaymentSystem.objects.filter(
            organization=organization
        ).first()

    @classmethod
    def is_configured(cls, organization: Organization) -> bool:
        return MaalyPayOrganizationPaymentSystem.objects.filter(
            organization=organization
        ).exists()

    @classmethod
    def connect_to_organization(
        cls,
        organization: Organization,
        merchant_id: str,
        api_key: str,
        bank_info: Optional[str] = None,
    ) -> dict:
        if not merchant_id or not api_key:
            raise BadRequestException(_("merchant_id and api_key are required"))

        try:
            with db_transaction.atomic():
                defaults = {
                    "merchant_id": merchant_id,
                    "api_key": api_key,
                }
                if bank_info:
                    defaults["bank_info"] = bank_info

                config, created = (
                    MaalyPayOrganizationPaymentSystem.objects.get_or_create(
                        organization=organization,
                        defaults=defaults,
                    )
                )

                if not created:
                    raise BadRequestException("You've already add this payment method")

                organization.maaly_pay_activated = True  # type: ignore
                organization.maaly_pay_confirmed = True  # type: ignore
                organization.save(update_fields=["maaly_pay_activated", "maaly_pay_confirmed"])  # type: ignore

                logger.info(
                    f"[MaalyPay] Connected to organization",
                    extra={
                        "org_id": organization.id,
                        "org_title": organization.title,
                        "merchant_id": merchant_id,
                        "has_bank_info": bool(bank_info),
                    }
                )

                result = {"merchant_id": merchant_id, "api_key": api_key, "created": True}
                if bank_info:
                    result["bank_info"] = bank_info
                return result
        except IntegrityError as e:
            logger.error(
                f"[MaalyPay] IntegrityError during connection",
                extra={"org_id": organization.id, "error": str(e)},
                exc_info=True
            )
            raise BadRequestException(_("You've already add this payment method"))

    @classmethod
    def create_payment(
        cls,
        api_key: str,
        merchant_id: int,
        amount: str,
        currency: str,
        description: str,
        merchant_tx_id: str,
        callback_url: str,
        customer_email: str,
        bank_info: Optional[str] = None,
    ) -> Optional[str]:
        url = f"{cls.BASE_URL}/create-payment-request"

        payload = {
            "merchantId": merchant_id,
            "fiatAmount": str(amount),
            "currency": currency,
            "description": description,
            "merchantTxId": merchant_tx_id,
            "merchantCallback": callback_url,
            "customerEmail": customer_email,
        }

        # Add optional bankInfo if provided
        if bank_info:
            payload["bankInfo"] = bank_info

        headers = {
            "Authorization": f"Bearer {api_key[:10]}***",  # Masked for security
            "Content-Type": "application/json",
        }

        logger.info(
            "[MaalyPay] Creating payment request",
            extra={
                "merchant_tx_id": merchant_tx_id,
                "amount": amount,
                "currency": currency,
                "has_bank_info": bool(bank_info),
                "merchant_id": merchant_id,
            }
        )

        # Log payload (without sensitive data)
        safe_payload = {**payload}
        logger.debug(
            "[MaalyPay] Request payload",
            extra={"payload": json.dumps(safe_payload, indent=2)}
        )

        # Temporary debug output for troubleshooting
        print(f"[MaalyPay DEBUG] Sending request to: {url}")
        print(f"[MaalyPay DEBUG] Merchant ID: {merchant_id} (type: {type(merchant_id).__name__})")
        print(f"[MaalyPay DEBUG] Amount: {amount} (type: {type(amount).__name__})")
        print(f"[MaalyPay DEBUG] Currency: {currency}")
        print(f"[MaalyPay DEBUG] Payload: {json.dumps(payload, indent=2)}")

        try:
            response = requests.post(
                url, json=payload, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, timeout=cls.TIMEOUT
            )

            logger.debug(
                "[MaalyPay] API Response",
                extra={
                    "status_code": response.status_code,
                    "response_body": response.text[:500],  # First 500 chars
                }
            )

            if response.status_code != 200:
                # Temporary debug output for troubleshooting
                print(f"[MaalyPay DEBUG] Status Code: {response.status_code}")
                print(f"[MaalyPay DEBUG] Response: {response.text}")
                print(f"[MaalyPay DEBUG] Merchant TX ID: {merchant_tx_id}")
                print(f"[MaalyPay DEBUG] Request Payload: {json.dumps(payload, indent=2)}")

                logger.error(
                    "[MaalyPay] Payment creation failed - non-200 status",
                    extra={
                        "status_code": response.status_code,
                        "response": response.text,
                        "merchant_tx_id": merchant_tx_id,
                    }
                )
                return None

            data = response.json()
            checkout_url = data.get("CheckoutUrl")

            if not checkout_url:
                logger.error(
                    "[MaalyPay] Missing CheckoutUrl in response",
                    extra={"response_data": data, "merchant_tx_id": merchant_tx_id}
                )
                return None

            logger.info(
                "[MaalyPay] Payment created successfully",
                extra={
                    "merchant_tx_id": merchant_tx_id,
                    "checkout_url": checkout_url[:100] + "...",
                }
            )
            return checkout_url

        except requests.Timeout as e:
            logger.error(
                "[MaalyPay] Request timeout",
                extra={
                    "merchant_tx_id": merchant_tx_id,
                    "timeout": cls.TIMEOUT,
                    "error": str(e),
                },
                exc_info=True
            )
            return None
        except requests.RequestException as e:
            logger.error(
                "[MaalyPay] Request failed",
                extra={
                    "merchant_tx_id": merchant_tx_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True
            )
            return None
        except Exception as e:
            logger.critical(
                "[MaalyPay] Unexpected error in create_payment",
                extra={
                    "merchant_tx_id": merchant_tx_id,
                    "error_type": type(e).__name__,
                    "error": str(e),
                },
                exc_info=True
            )
            return None

    @classmethod
    def check_status(
        cls, api_key: str, merchant_tx_id: str
    ) -> Optional[MaalyPayOrderStatus]:
        url = f"{cls.BASE_URL}/check-online-transaction-merch/{merchant_tx_id}"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        logger.debug(
            "[MaalyPay] Checking payment status",
            extra={"merchant_tx_id": merchant_tx_id}
        )

        try:
            response = requests.get(url, headers=headers, timeout=cls.TIMEOUT)

            logger.debug(
                "[MaalyPay] Status check response",
                extra={
                    "status_code": response.status_code,
                    "merchant_tx_id": merchant_tx_id,
                }
            )

            if response.status_code != 200:
                logger.warning(
                    "[MaalyPay] Non-200 status code on check",
                    extra={
                        "status_code": response.status_code,
                        "merchant_tx_id": merchant_tx_id,
                        "response": response.text[:200],
                    }
                )
                return None

            data = response.json()

            logger.info(
                "[MaalyPay] Payment status retrieved",
                extra={
                    "merchant_tx_id": merchant_tx_id,
                    "status": data.get('status'),
                    "fiat_amount": data.get('fiatAmount'),
                    "filled_amount": data.get('filledAmount'),
                    "has_tx_hash": bool(data.get('txHash')),
                }
            )
            return data

        except requests.Timeout as e:
            logger.error(
                "[MaalyPay] Status check timeout",
                extra={
                    "merchant_tx_id": merchant_tx_id,
                    "timeout": cls.TIMEOUT,
                },
                exc_info=True
            )
            return None
        except requests.RequestException as e:
            logger.error(
                "[MaalyPay] Status check request failed",
                extra={
                    "merchant_tx_id": merchant_tx_id,
                    "error": str(e),
                },
                exc_info=True
            )
            return None
        except json.JSONDecodeError as e:
            logger.error(
                "[MaalyPay] Invalid JSON in status response",
                extra={
                    "merchant_tx_id": merchant_tx_id,
                    "response_text": response.text[:200],
                },
                exc_info=True
            )
            return None

    @classmethod
    def is_paid(cls, api_key: str, merchant_tx_id: str) -> bool:
        status_data = cls.check_status(api_key, merchant_tx_id)
        if status_data is None:
            return False
        return status_data.get("status") is True

    @classmethod
    def generate_merchant_tx_id(cls, transaction_id: int) -> str:
        import time
        timestamp = int(time.time())
        return f"apofiz-{transaction_id}-{timestamp}"
