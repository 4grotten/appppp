import logging
import os
from datetime import datetime
from decimal import Decimal

from django.conf import settings

from organizations.models import (
    OrganizationInvoiceInfo,
    UserOrgSubscription,
)
from organizations.serializers.invoice_serializers import (
    OrganizationInvoiceInfoSerializer,
)
from organizations.services.invoice_service import InvoiceDataService
from transactions.models import Transaction

logger = logging.getLogger(__name__)


class ReceiptService:

    @staticmethod
    def create_receipt_from_crypto_cloud(org_subs: UserOrgSubscription):
        from organizations.tasks import create_invoice_pdf

        tariff = org_subs.tariff
        sub_id = org_subs.pk
        country_data = InvoiceDataService.get_country_invoice_data(tariff)
        serializer = OrganizationInvoiceInfoSerializer(
            OrganizationInvoiceInfo.objects.get(
                organization_id=org_subs.organization.pk
            )
        )

        logo_path = os.path.join(settings.BASE_DIR, "static", "images", "apofiz.png")

        context = {
            "country_data": country_data,
            "data": serializer.data,
            "title": "receipt",
            "invoice_number": "",
            "invoice_date": datetime.now().strftime("%d-%m-%Y"),
            "payment_method": "CryptoCloud",
            "logo_path": f"file://{logo_path}",
            "subscription_id": sub_id,
        }
        create_invoice_pdf.delay(context=context)

    @staticmethod
    def create_receipt_from_management_as_crypto_cloud(
        org_subs: UserOrgSubscription, inv_org_info: OrganizationInvoiceInfo
    ):
        from organizations.tasks import create_invoice_pdf

        tariff = org_subs.tariff
        sub_id = org_subs.pk
        country_data = InvoiceDataService.get_country_invoice_data(tariff)
        serializer = OrganizationInvoiceInfoSerializer(inv_org_info)

        logo_path = os.path.join(settings.BASE_DIR, "static", "images", "apofiz.png")

        context = {
            "country_data": country_data,
            "data": serializer.data,
            "title": "receipt",
            "invoice_number": "",
            "invoice_date": datetime.now().strftime("%d%m%Y"),
            "payment_method": "CryptoCloud",
            "logo_path": f"file://{logo_path}",
            "subscription_id": sub_id,
        }
        create_invoice_pdf.delay(context=context)

    @staticmethod
    def create_receipt_from_maalypay(org_subs: UserOrgSubscription):
        from organizations.tasks import create_invoice_pdf

        """
        Generate receipt for MaalyPay payment.

        Args:
            org_subs: UserOrgSubscription instance
        """
        tariff = org_subs.tariff
        sub_id = org_subs.pk
        country_data = InvoiceDataService.get_country_invoice_data(tariff)
        serializer = OrganizationInvoiceInfoSerializer(
            OrganizationInvoiceInfo.objects.get(
                organization_id=org_subs.organization.pk
            )
        )

        logo_path = os.path.join(settings.BASE_DIR, "static", "images", "apofiz.png")

        context = {
            "country_data": country_data,
            "data": serializer.data,
            "title": "receipt",
            "invoice_number": "",
            "invoice_date": datetime.now().strftime("%d-%m-%Y"),
            "payment_method": "MaalyPay",
            "logo_path": f"file://{logo_path}",
            "subscription_id": sub_id,
        }
        create_invoice_pdf.delay(context=context)

    @staticmethod
    def create_receipt_for_assistant(transaction_obj: Transaction, payment_method: str = "Online") -> None:
        """Generate receipt for AI assistant payment."""
        from organizations.tasks import create_invoice_pdf

        organization = transaction_obj.organization
        amount = transaction_obj.original_amount or Decimal("0")
        currency_code = transaction_obj.currency.code if transaction_obj.currency else "USD"

        # Get tax info from organization's country
        tax = Decimal("0")
        tax_amount = Decimal("0")
        code = "AI"
        try:
            invoice_info = organization.country.invoice_info
            tax = Decimal(str(invoice_info.tax))
            tax_amount = amount * tax / Decimal("100")
            code = organization.country.code
        except Exception:
            logger.warning(
                f"[RECEIPT] No invoice_info for org {organization.id} country"
            )

        country_data = {
            "code": code,
            "amount": str(amount),
            "tax_amount": str(tax_amount),
            "currency": currency_code,
            "tax": str(tax),
        }

        # Try to get organization invoice info for receipt template
        org_info = OrganizationInvoiceInfo.objects.filter(
            organization_id=organization.pk
        ).first()
        data = OrganizationInvoiceInfoSerializer(org_info).data if org_info else {}

        logo_path = os.path.join(settings.BASE_DIR, "static", "images", "apofiz.png")

        context = {
            "country_data": country_data,
            "data": data,
            "title": "receipt",
            "invoice_number": "",
            "invoice_date": datetime.now().strftime("%d-%m-%Y"),
            "payment_method": payment_method,
            "logo_path": f"file://{logo_path}",
            "transaction_id": transaction_obj.pk,
        }
        create_invoice_pdf.delay(context=context)
