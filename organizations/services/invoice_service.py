from organizations.models import RegionalTariff, Invoice
from organizations.models import OrganizationInvoiceInfo, Organization
from organizations.tasks import create_invoice_pdf
from django.forms.models import model_to_dict
from users.models import User
from decimal import Decimal
import os
from django.conf import settings


class InvoiceDataService:
    """Сервис для получения данных о счёте и стране"""

    @staticmethod
    def get_country_invoice_data(tariff: RegionalTariff) -> dict:

        invoice_info = tariff.country.invoice_info

        data = {
            "name": invoice_info.name,
            "country": tariff.country.name,
            "city": invoice_info.city,
            "address": invoice_info.address,
            "email": invoice_info.email,
            "price": tariff.original_price,
            "code": tariff.country.code,
            "currency": tariff.country.currency.code,
            "tariff": tariff.tariff_type,
            "tax": invoice_info.tax,
            "tax_id": invoice_info.tax_id,
        }

        # Рассчёт суммы с учётом налога
        if data["tax"] == 0:
            data.pop("tax")
            data.pop("tax_id")
            data["amount"] = data["price"]
        else:
            tax_decimal = Decimal(str(data["tax"])) / Decimal("100")
            data["tax_amount"] = data["price"] * tax_decimal
            data["amount"] = data["price"] + data["tax_amount"]
            data["tax_amount"] = format(data["tax_amount"], ",.2f")

        data["price"] = format(data["price"], ",.2f")
        data["amount"] = format(data["amount"], ",.2f")

        return data

    @staticmethod
    def get_tariff(tariff_id: int):
        tariff = (
            RegionalTariff.objects.filter(id=tariff_id)
            .select_related("country__currency")
            .prefetch_related("country__invoice_info")
            .get()
        )
        return tariff


class OrganizationInvoiceService:

    @classmethod
    def create_invoice(
        cls,
        invoice_type: str,
        tariff_id: int,
        data: dict,
        organization: int,
        payment_method: str,
        user: User,
    ) -> None:
        if not invoice_type:
            raise ValueError("Invoice type is required")
        data["organization"] = Organization.objects.get(id=organization)
        tariff = InvoiceDataService.get_tariff(tariff_id)
        country_data = InvoiceDataService.get_country_invoice_data(tariff)
        data = cls.get_or_create_info(data)

        invoice = OrganizationInvoiceService._create_invoice_object(
            user=user,
            code=country_data["code"],
            org_info=data.get("object"),
            amount=Decimal(country_data.get("amount").replace(",", "")),
            tariff=tariff,
            tax_amount=Decimal(country_data.get("tax_amount", 0).replace(",", "")),
        )

        context = cls._build_invoice_context(
            invoice, invoice_type, country_data, data.get("data"), payment_method
        )
        create_invoice_pdf.delay(
            invoice.invoice_number,
            context,
        )

    @staticmethod
    def _create_invoice_object(
        code: str,
        org_info: OrganizationInvoiceInfo,
        amount: Decimal,
        tariff: RegionalTariff,
        tax_amount: Decimal,
        user: User,
    ) -> Invoice:
        invoice = Invoice(
            code=code,
            organization_info=org_info,
            invoice_amount=amount,
            tariff=tariff,
            invoice_tax=tax_amount,
            user=user,
        )
        invoice.save()
        return invoice

    @staticmethod
    def get_or_create_info(user_data: dict):
        organization_info, created = OrganizationInvoiceInfo.objects.get_or_create(
            **user_data
        )
        return {"data": model_to_dict(organization_info), "object": organization_info}

    @staticmethod
    def _build_invoice_context(
        invoice: Invoice,
        invoice_type: str,
        country_data: dict,
        user_data: dict,
        payment_method: str,
    ) -> dict:
        logo_path = os.path.join(settings.BASE_DIR, "static", "images", "apofiz.png")

        context = {
            "country_data": country_data,
            "data": user_data,
            "title": "invoice",
            "invoice_number": invoice.invoice_number,
            "invoice_date": invoice.created_at.strftime("%d-%m-%Y"),
            "payment_method": payment_method,
            "logo_path": f"file://{logo_path}",
            "extra_info": f"{invoice_type}-info",
        }

        return context
