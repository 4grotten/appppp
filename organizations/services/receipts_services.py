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
        country_data = InvoiceDataService.get_country_invoice_data(tariff)
        data = OrganizationInvoiceInfoSerializer(
            OrganizationInvoiceInfo.objects.get(
                organization_id=org_subs.organization.pk
            )
        )

        logo_path = os.path.join(settings.BASE_DIR, "static", "images", "apofiz.png")

        context = {
            "country_data": country_data,
            "data": data,
            "title": "receipt",
            "invoice_number": "",
            "invoice_date": datetime.now().strftime("%d%m%Y"),
            "payment_method": "CryptoCloud",
            "logo_path": f"file://{logo_path}",
            "extra_info": "",
        }
        create_invoice_pdf.delay(context=context)
