from datetime import datetime
from organizations.models import RegionalTariff, Invoice
from organizations.models import (
    OrganizationInvoiceInfo,
    Organization,
    UserOrgSubscription,
)
from organizations.tasks import create_invoice_pdf
from common.exceptions import InvoiceInfoDoesNotExists
from mailer.services import MailerService
from rest_framework.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from django.forms.models import model_to_dict
from django.db.models import Q
from users.models import User
from decimal import Decimal
import os
from typing import Union
from django.conf import settings


class InvoiceDataService:
    """Сервис для получения данных о счёте и стране"""

    @staticmethod
    def get_country_invoice_data(tariff: RegionalTariff) -> dict:
        try:
            invoice_info = tariff.country.invoice_info
        except Exception as e:
            raise InvoiceInfoDoesNotExists

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
    def _user_permission(cls, user, organization_id):
        return (
            Organization.objects.filter(id=organization_id)
            .filter(Q(owner=user) | Q(memberships__user=user))
            .exists()
        )

    @classmethod
    def create_invoice(
        cls,
        invoice_type: str,
        tariff_id: int,
        data: dict,
        organization: int,
        payment_method: str,
        user: User,
    ):
        if not invoice_type:
            raise ValueError("Invoice type is required")

        if not cls._user_permission(user, organization):
            raise PermissionDenied(
                {"message": _("You are not an memberships of this organization")}
            )
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

        return invoice.invoice_number

    @staticmethod
    def _create_invoice_object(
        code: str,
        org_info: Union[OrganizationInvoiceInfo, None],
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

    @classmethod
    def get_invoice_by_invoice_number(cls, invoice_number: str) -> Union[Invoice, None]:
        qs = (
            Invoice.objects.filter(invoice_number=invoice_number)
            .select_related("user", "organization_info", "subscription", "tariff")
            .first()
        )
        return qs

    @classmethod
    def get_invoice_informations_list(cls, organization_id: int, user: User, info_type):
        if not cls._user_permission(user, organization_id):
            raise PermissionDenied(
                {"message": _("You are not an memberships of this organization")}
            )
        if info_type.lower() == "owner":
            information_qs = OrganizationInvoiceInfo.objects.filter(
                organization_id=organization_id, company_name__isnull=True
            )
        elif info_type.lower() == "company":
            information_qs = OrganizationInvoiceInfo.objects.filter(
                organization_id=organization_id, company_name__isnull=False
            ).exclude(company_name="")

        else:
            raise ValueError("You need to choose true type of invoice information")

        return information_qs

    @classmethod
    def get_invoice_information(cls, user, info_id):
        if (
            not Organization.objects.filter(invoice_info__id=info_id)
            .filter(Q(owner=user) | Q(memberships__user=user))
            .exists()
        ):
            raise PermissionDenied(
                {"message": _("You are not an memberships of this organization")}
            )

        information_qs = OrganizationInvoiceInfo.objects.get(pk=info_id)

        return information_qs

    @classmethod
    def get_invoice_list(cls, user, organization_id):
        if not cls._user_permission(user, organization_id):
            raise PermissionDenied(
                {"message": _("You are not an memberships of this organization")}
            )

        qs = Invoice.objects.filter(
            organization_info__organization_id=organization_id
        ).exclude(receipt_pdf__isnull=False)

        return qs

    @classmethod
    def get_invoice(cls, user, invoice_id): ...

    @classmethod
    def get_receipt_list(cls, user, organization_id):
        if not cls._user_permission(user, organization_id):
            raise PermissionDenied(
                {"message": _("You are not an memberships of this organization")}
            )

        qs = Invoice.objects.filter(
            organization_info__organization_id=organization_id,
            receipt_pdf__isnull=False,
        ).exclude(receipt_pdf="")

        return qs

    @classmethod
    def get_active_tariff(cls, organization_id):
        qs = UserOrgSubscription.objects.filter(
            organization_id=organization_id, is_active=True
        ).select_related("tariff")

        return qs

    @staticmethod
    def send_to_email(invoice_id):
        invoice_qs = Invoice.objects.select_related("organization_info").get(
            pk=invoice_id
        )
        invoice_url = invoice_qs.invoice_pdf
        invoice_email = invoice_qs.organization_info.address
        MailerService.send_invoice_url_email(invoice_email, invoice_url, datetime.now())

        return {"message": "successfully sent"}
