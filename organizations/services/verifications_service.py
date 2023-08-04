from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException
from organizations.models import OrganizationVerificationUsers, Organization, OrganizationPaymentSystemUsers


class VerificationService:
    model = OrganizationVerificationUsers

    @classmethod
    def create(cls, organization: Organization, username: str, phone_number: str, email: str):
        try:
            verification = cls.model.objects.filter(organization=organization).exists()
            if verification:
                verification = cls.model.objects.get(organization=organization)
                verification.phone_number = phone_number
                verification.username = username
                verification.email = email
                verification.save()
            else:
                cls.model.objects.create(organization=organization, username=username, phone_number=phone_number,
                                         email=email)
        except Exception as e:
            raise BadRequestException(_(f'{e}'))


class PaymentSystemConfirmationService:
    model = OrganizationPaymentSystemUsers

    @classmethod
    def create(cls, organization: Organization, username: str, phone_number: str, email: str, payment_system_id: int):
        try:
            confirmation = cls.model.objects.filter(organization=organization).exists()
            if confirmation:
                confirmation = cls.model.objects.get(organization=organization)
                confirmation.phone_number = phone_number
                confirmation.username = username
                confirmation.email = email
                confirmation.save()
            else:
                cls.model.objects.create(organization=organization, username=username, phone_number=phone_number,
                                         email=email)
        except Exception as e:
            raise BadRequestException(_(f'{e}'))
