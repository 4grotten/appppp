from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException
from organizations.models import OrganizationVerificationUsers, Organization


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
