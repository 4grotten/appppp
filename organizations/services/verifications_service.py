from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException
from organizations.models import (
    Organization,
    OrganizationPaymentSystemUsers,
    OrganizationVerificationUsers,
)


class VerificationService:
    model = OrganizationVerificationUsers

    @classmethod
    def create(
        cls, organization: Organization, username: str, phone_number: str, email: str
    ):
        try:
            verification = cls.model.objects.filter(organization=organization).exists()
            if verification:
                verification = cls.model.objects.get(organization=organization)
                verification.phone_number = phone_number
                verification.username = username
                verification.email = email
                verification.save()
            else:
                cls.model.objects.create(
                    organization=organization,
                    username=username,
                    phone_number=phone_number,
                    email=email,
                )
        except Exception as e:
            raise BadRequestException(_(f"{e}"))


class PaymentSystemConfirmationService:
    """Сервис для подключения платёжных систем к организации"""

    model = OrganizationPaymentSystemUsers

    @classmethod
    def create(
        cls,
        organization: Organization | None = None,
        username: str | None = None,
        phone_number: str | None = None,
        email: str | None = None,
        payment_system_id: int | None = None,
        merchant_id: str | None = None,
        api_key: str | None = None,
    ):
        if payment_system_id == 6:
            if organization is None:
                raise BadRequestException(
                    _("Organization is required for this payment system")
                )
            if merchant_id is None or api_key is None:
                raise BadRequestException(
                    _("merchant_id and api_key are required for MaalyPay")
                )

            from organizations.services.maalypay_service import MaalyPayService

            return MaalyPayService.connect_to_organization(
                organization=organization,
                merchant_id=merchant_id,
                api_key=api_key,
            )

        if organization is None:
            raise BadRequestException(_("Organization is required"))
        if username is None or phone_number is None or email is None:
            raise BadRequestException(
                _("username, phone_number and email are required")
            )

        return cls._create_generic(organization, username, phone_number, email)

    @classmethod
    def _create_generic(
        cls,
        organization: Organization,
        username: str,
        phone_number: str,
        email: str,
    ):
        try:
            obj, created = cls.model.objects.update_or_create(
                organization=organization,
                defaults={
                    "username": username,
                    "phone_number": phone_number,
                    "email": email,
                },
            )
            return obj
        except Exception as e:
            print(f"PaymentSystemConfirmationService error: {e}")
            raise BadRequestException(str(e))
