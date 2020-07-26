from typing import Union

from django.db import IntegrityError
from django.db.models import QuerySet

from common.exceptions import NotAcceptableException, IntegrityException, ObjectNotFoundException
from organizations.models import Organization, Partnership
from organizations.services.organization_services import OrganizationService
from users.models import User


class PartnershipService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Partnership.objects.get(*args, **kwargs)
        except Partnership.DoesNotExist:
            raise ObjectNotFoundException('Partnership not found')

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
    def are_partners(cls, requested_by: Organization, accepted_by: Organization) -> bool:
        return Partnership.objects.filter(requested_by=requested_by, accepted_by=accepted_by, is_accepted=True).exists()

    @classmethod
    def get_organization_partnerships(cls, organization: Organization, user: User) -> QuerySet:
        if not OrganizationService.user_can_edit_partner(organization=organization, user=user):
            raise NotAcceptableException('No access to partner settings')

        return Partnership.objects.filter(requested_by=organization)

    @classmethod
    def get_available_partnerships(cls, partnership_id: int, user: User) -> Union[QuerySet, None]:
        partnership = cls.get(id=partnership_id)
        try:
            return cls.get_organization_partnerships(organization=partnership.requested_by, user=user)
        except NotAcceptableException:
            return None

    @classmethod
    def set_permissions(cls, partnership: Partnership, can_check_attendance: bool, can_see_stats: bool,
                        can_edit_organization: bool) -> Partnership:
        try:
            partnership.is_accepted = True
            partnership.can_check_attendance = can_check_attendance
            partnership.can_see_stats = can_see_stats
            partnership.can_edit_organization = can_edit_organization
            partnership.save()
            return partnership
        except IntegrityError:
            raise IntegrityException('Could not update partnership permissions')
