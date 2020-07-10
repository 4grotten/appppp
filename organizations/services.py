from itertools import groupby

from django.contrib.gis.geos import Point
from django.db import transaction
from django.db.models import QuerySet

from common.exceptions import ObjectNotFoundException, NotAcceptableException, ValidationException
from users.models import User
from .models import Organization, Membership, PhoneNumber, SocialNetworkContact, DiscountCard


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
    def user_can_edit_organization(cls, organization_id: int, user: User) -> bool:
        organization = OrganizationService.get(id=organization_id)
        if organization.owner == user:
            return True
        try:
            membership = MembershipService.get(organization=organization, user=user)
        except ObjectNotFoundException:
            return False
        return membership.role.can_edit_organization

    @classmethod
    def set_location(cls, organization, longitude, latitude, address):
        try:
            point = Point(longitude, latitude)
            organization.location = point
            organization.address = address
            organization.save()

            return organization

        except Exception:
            raise ValidationException('Something went wrong')

    @classmethod
    def create_organization(cls, owner, title, description, image_id,
                            opens_at, closes_at, address, longitude, latitude,
                            types, numbers, accounts, cards, currency="SDD"):
        with transaction.atomic():
            point = Point(longitude, latitude)
            organization = Organization.objects.create(owner=owner, title=title, description=description,
                                                       image_id=image_id, opens_at=opens_at, closes_at=closes_at,
                                                       address=address, location=point, currency=currency)
            organization.types.set(types)
            for number in numbers:
                OrgPhoneNumberService.create(organization=organization, number=number)
            for link in accounts:
                OrgSocialNetworkContactService.create(organization=organization, url=link)

            DiscountCardService.bulk_create_discounts(cards=cards, organization=organization)

            return organization


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
    def create(cls, organization: Organization, number: str) -> PhoneNumber:
        return PhoneNumber.objects.create(organization=organization, phone_number=number)

    @classmethod
    def get_numbers_of_organization(cls, organization_id: int) -> QuerySet:
        return PhoneNumber.objects.filter(organization_id=organization_id)

    @classmethod
    def update_phone_numbers(cls, organization_id: int, user: User, numbers: list):
        if not OrganizationService.user_can_edit_organization(organization_id=organization_id, user=user):
            raise NotAcceptableException('No rights to edit organization')

        with transaction.atomic():
            PhoneNumber.objects.filter(organization_id=organization_id).delete()
            numbers = [PhoneNumber(organization_id=organization_id, phone_number=number) for number in numbers]
            PhoneNumber.objects.bulk_create(numbers)
            return numbers


class OrgSocialNetworkContactService:
    model = SocialNetworkContact

    @classmethod
    def create(cls, organization: Organization, url: str) -> PhoneNumber:
        return SocialNetworkContact.objects.create(organization=organization, url=url)

    @classmethod
    def get_networks_of_organization(cls, organization_id: int) -> QuerySet:
        return SocialNetworkContact.objects.filter(organization_id=organization_id)

    @classmethod
    def update_social_networks(cls, organization_id: int, user: User, urls: list):
        if not OrganizationService.user_can_edit_organization(organization_id=organization_id, user=user):
            raise NotAcceptableException('No rights to edit organization')

        with transaction.atomic():
            SocialNetworkContact.objects.filter(organization_id=organization_id).delete()
            contacts = [SocialNetworkContact(organization_id=organization_id, url=url) for url in urls]
            SocialNetworkContact.objects.bulk_create(contacts)
            return contacts


class DiscountCardService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return DiscountCard.objects.get(**kwargs)
        except DiscountCard.DoesNotExist:
            raise ObjectNotFoundException('Discount not found')

    @classmethod
    def get_grouped_discounts(cls, organization_id: int) -> dict:
        discounts = DiscountCard.objects.filter(organization_id=organization_id)
        discounts_dict = {
            DiscountCard.CUMULATIVE: [],
            DiscountCard.FIXED: []
        }

        for discount_type, group in groupby(discounts, lambda x: x.type):
            discounts_dict[discount_type] = list(group)

        return discounts_dict

    @classmethod
    def delete_discount(cls, discount_id: int, user: User):
        discount = cls.get(id=discount_id)
        if not OrganizationService.user_can_edit_organization(organization_id=discount.organization.id, user=user):
            raise NotAcceptableException('No rights to edit organization')
        discount.delete()

    @classmethod
    def bulk_create_discounts(cls, cards: list, organization: Organization):
        for card_data in cards:
            if card_data['type'] == DiscountCard.CUMULATIVE:
                card_data['currency'] = organization.currency
            DiscountCard.objects.create(organization=organization, **card_data)
