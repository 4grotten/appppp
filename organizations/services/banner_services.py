from django.db import IntegrityError

from common.exceptions import NotAcceptableException, IntegrityException
from common.models import File
from organizations.models import Banner, Organization
from organizations.services.organization_services import OrganizationService
from organizations.services.partnership_services import PartnershipService
from users.models import User


class BannerService:
    @classmethod
    def create(cls, *args, **kwargs):
        try:
            Banner.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException('Could not save banner')

    @classmethod
    def get_banners(cls, organization: Organization):
        return Banner.objects.filter(host_organization=organization).order_by('-updated_at')

    @classmethod
    def create_banner(cls, user: User, host: Organization, linked_to: Organization, image: File):
        if not OrganizationService.user_can_edit_partner(user=user, organization=host):
            raise NotAcceptableException('No access to partner settings')
        if not PartnershipService.are_partners(requested_by=host, accepted_by=linked_to):
            raise NotAcceptableException('The organizations are not partners')

        cls.create(host_organization=host, linked_organization=linked_to, image=image)

    @classmethod
    def delete_banner(cls, user: User, banner: Banner):
        if not OrganizationService.user_can_edit_partner(user=user, organization=banner.host_organization):
            raise NotAcceptableException('No access to partner settings')
        banner.delete()
