from organizations.models import (
    UserOrgSubscription,
    RegionalTariff,
    OrganizationInvoiceInfo,
)
from users.models import User
from common.models import Country, CountryInvoiceInfo
from datetime import datetime
from organizations.services.invoice_service import InvoiceDataService
from organizations.serializers.invoice_serializers import (
    OrganizationInvoiceInfoSerializer,
)
import os
from django.conf import settings
from organizations.tasks import create_invoice_pdf


class ReceiptService:

    @staticmethod
    def create_receipt_from_crypto_cloud(org_subs: UserOrgSubscription):
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
            "invoice_date": datetime.now().strftime("%d%m%Y"),
            "payment_method": "CryptoCloud",
            "logo_path": f"file://{logo_path}",
            "subscription_id": sub_id,
        }
        create_invoice_pdf.delay(context=context)

    @staticmethod
    def create_receipt_from_management_as_crypto_cloud(
        org_subs: UserOrgSubscription, inv_org_info: OrganizationInvoiceInfo
    ):
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
