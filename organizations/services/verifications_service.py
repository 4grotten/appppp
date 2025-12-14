from typing import Union

from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException
from organizations.models import (
    MaalyPayOrganizationPaymentSystem,
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
    model = OrganizationPaymentSystemUsers
    maalypay = MaalyPayOrganizationPaymentSystem

    @classmethod
    def create(
        cls,
        organization: Union[Organization, None] = None,
        username: Union[str, None] = None,
        phone_number: Union[str, None] = None,
        email: Union[str, None] = None,
        payment_system_id: Union[int, None] = None,
        merchant_id: Union[str, None] = None,
        api_key: Union[str, None] = None,
    ):
        if payment_system_id == 6:
            if cls.maalypay.objects.filter(organization=organization).exists():
                raise BadRequestException("You've already add this payment method")
            maalypay = cls.maalypay.objects.create(
                merchant_id=merchant_id, api_key=api_key, organization=organization
            )
            organization.maaly_pay_activated = True  # type: ignore
            organization.save()  # type: ignore
            return {"merchant_id": merchant_id, "api_key": api_key, "created": True}
        try:
            confirmation = cls.model.objects.filter(organization=organization).exists()
            if confirmation:
                confirmation = cls.model.objects.get(organization=organization)
                confirmation.phone_number = phone_number
                confirmation.username = username
                confirmation.email = email
                confirmation.save()
            else:
                cls.model.objects.create(
                    organization=organization,
                    username=username,
                    phone_number=phone_number,
                    email=email,
                )
        except Exception as e:
            raise BadRequestException(_(f"{e}"))
