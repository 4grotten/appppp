from typing import Optional, TypedDict

import requests
from django.db import IntegrityError
from django.db import transaction as db_transaction
from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException
from organizations.models import (
    MaalyPayOrganizationPaymentSystem,
    Organization,
)


class MaalyPayOrderStatus(TypedDict):
    fiatAmount: str
    status: bool
    filledAmount: str
    txHash: str | None
    network: str | None
    asset: str | None
    txLink: str | None


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
    ) -> dict:
        if not merchant_id or not api_key:
            raise BadRequestException(_("merchant_id and api_key are required"))

        try:
            with db_transaction.atomic():
                config, created = (
                    MaalyPayOrganizationPaymentSystem.objects.get_or_create(
                        organization=organization,
                        defaults={
                            "merchant_id": merchant_id,
                            "api_key": api_key,
                        },
                    )
                )

                if not created:
                    raise BadRequestException("You've already add this payment method")

                organization.maaly_pay_activated = True  # type: ignore
                organization.save(update_fields=["maaly_pay_activated"])  # type: ignore

                print(f"{organization.maaly_pay_activated}")
                return {"merchant_id": merchant_id, "api_key": api_key, "created": True}
        except IntegrityError:
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

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        print(f"MaalyPay: Creating payment, merchantTxId={merchant_tx_id}")

        try:
            response = requests.post(
                url, json=payload, headers=headers, timeout=cls.TIMEOUT
            )

            if response.status_code != 200:
                print(f"MaalyPay: Error {response.status_code} - {response.text}")
                return None

            data = response.json()
            checkout_url = data.get("CheckoutUrl")

            if not checkout_url:
                print(f"MaalyPay: No CheckoutUrl in response: {data}")
                return None

            print(f"MaalyPay: Payment created, url={checkout_url[:50]}...")
            return checkout_url

        except requests.Timeout:
            print("MaalyPay: Request timeout")
            return None
        except requests.RequestException as e:
            print(f"MaalyPay: Request failed: {e}")
            return None
        except Exception as e:
            print(f"MaalyPay: Unexpected error: {e}")
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

        try:
            response = requests.get(url, headers=headers, timeout=cls.TIMEOUT)

            if response.status_code != 200:
                print(f"MaalyPay: Check status error {response.status_code}")
                return None

            data = response.json()
            print(f"MaalyPay: Status for {merchant_tx_id}: {data.get('status')}")
            return data

        except requests.Timeout:
            print("MaalyPay: Check status timeout")
            return None
        except requests.RequestException as e:
            print(f"MaalyPay: Check status failed: {e}")
            return None

    @classmethod
    def is_paid(cls, api_key: str, merchant_tx_id: str) -> bool:
        status_data = cls.check_status(api_key, merchant_tx_id)
        if status_data is None:
            return False
        return status_data.get("status") is True

    @classmethod
    def generate_merchant_tx_id(cls, transaction_id: int) -> str:
        return f"apofiz-{transaction_id}"
