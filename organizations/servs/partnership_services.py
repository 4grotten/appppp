from django.db import IntegrityError
from django.db.models import QuerySet

from common.exceptions import NotAcceptableException, IntegrityException
from organizations.models import Organization, Partnership
from organizations.services import OrganizationService
from users.models import User


class PartnershipService:
    @classmethod
    def create(cls, *args, **kwargs):
        try:
            Partnership.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException('Could not create partnership request')

    @classmethod
    def create_request(cls, user: User, requested_by: Organization, accepted_by: Organization):
        if not OrganizationService.user_can_edit_organization(organization_id=requested_by.id, user=user):
            raise NotAcceptableException('No rights to edit organization')
        cls.create(requested_by=requested_by, accepted_by=accepted_by)
        # ToDo: send notification to accepted_by organization

    @classmethod
    def get_accepted_partners(cls, user: User, organization: Organization) -> QuerySet:
        if not OrganizationService.user_can_edit_organization(organization_id=organization.id, user=user):
            raise NotAcceptableException('No rights to edit organization')

        partners = Organization.objects.filter(
            id__in=organization.requested_partnerships.filter(
                requested_by=organization).filter(is_accepted=True).values_list('accepted_by', flat=True))

        return partners
