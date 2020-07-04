from django.db import transaction
from django.db.models import QuerySet

from common.exceptions import ObjectNotFoundException, NotAcceptableException
from users.models import User

from .models import Organization, Membership, PhoneNumber, SocialNetworkContact


class OrganizationService:
    model = Organization

    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return cls.model.objects.get(**kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException('Organization not found')

    @classmethod
    def get_user_role_in_organization(cls, organization: Organization, user: User) -> str:
        if organization.owner == user:
            return 'Собственник'
        membership = MembershipService.get(organization=organization, user=user)
        return membership.role.title

    @classmethod
    def user_can_edit_organization(cls, organization: Organization, user: User) -> bool:
        if organization.owner == user:
            return True
        membership = MembershipService.get(organization=organization, user=user)
        return membership.role.can_edit_organization


class MembershipService:
    model = Membership

    @classmethod
    def get(cls, *args, **kwargs) -> Membership:
        try:
            return cls.model.objects.get(*args, **kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException('Membership not found')


class OrgPhoneNumberService:
    model = PhoneNumber

    @classmethod
    def get_numbers_of_organization(cls, organization_id: int) -> QuerySet:
        return PhoneNumber.objects.filter(organization_id=organization_id)

    @classmethod
    def update_phone_numbers(cls, organization_id: int, user: User, numbers: list):
        organization = OrganizationService.get(id=organization_id)
        if not OrganizationService.user_can_edit_organization(organization=organization, user=user):
            raise NotAcceptableException('No rights to edit organization')

        with transaction.atomic():
            PhoneNumber.objects.filter(organization=organization).delete()
            numbers = [PhoneNumber(organization=organization, phone_number=number) for number in numbers]
            PhoneNumber.objects.bulk_create(numbers)
            return numbers


class OrgSocialNetworkContactService:
    model = SocialNetworkContact

    @classmethod
    def get_networks_of_organization(cls, organization_id: int) -> QuerySet:
        return SocialNetworkContact.objects.filter(organization_id=organization_id)

    @classmethod
    def update_social_networks(cls, organization_id: int, user: User, urls: list):
        organization = OrganizationService.get(id=organization_id)
        if not OrganizationService.user_can_edit_organization(organization=organization, user=user):
            raise NotAcceptableException('No rights to edit organization')

        with transaction.atomic():
            SocialNetworkContact.objects.filter(organization=organization).delete()
            contacts = [SocialNetworkContact(organization=organization, url=url) for url in urls]
            SocialNetworkContact.objects.bulk_create(contacts)
            return contacts
