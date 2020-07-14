from itertools import groupby
from typing import Tuple, Union

from django.contrib.gis.geos import Point
from django.db import transaction, IntegrityError
from django.db.models import QuerySet

from common.exceptions import ObjectNotFoundException, NotAcceptableException, ValidationException, IntegrityException
from users.models import User
from .models import Organization, Membership, PhoneNumber, SocialNetworkContact, DiscountCard, Subscription, \
    CardOwnership


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
    def user_can_sell(cls, organization: Organization, user: User) -> bool:
        if organization.owner == user:
            return True
        try:
            membership = MembershipService.get(organization=organization, user=user)
        except ObjectNotFoundException:
            return False
        return membership.role.can_sale

    @classmethod
    def get_user_permissions_dict(cls, organization: Organization, user: User) -> dict:
        if organization.owner == user:
            return {
                'is_owner': True,
                'can_sale': True,
                'can_check_attendance': True,
                'can_see_stats': True,
                'can_edit_organization': True
            }

        try:
            role = MembershipService.get(organization=organization, user=user).role
            return {
                'is_owner': False,
                'can_sale': role.can_sale,
                'can_check_attendance': role.can_check_attendance,
                'can_see_stats': role.can_see_stats,
                'can_edit_organization': role.can_edit_organization
            }
        except ObjectNotFoundException:
            return {
                'is_owner': False,
                'can_sale': False,
                'can_check_attendance': False,
                'can_see_stats': False,
                'can_edit_organization': False
            }

    @classmethod
    def get_partners_dict(cls, organization: Organization) -> Tuple[int, QuerySet]:
        # ToDo: implement this after organizations partnerships
        partners = Organization.objects.all()
        partners_list = []

        for partner in partners[:3]:
            partners_list.append({'id': partner.id, 'image': partner.image})

        return partners.count(), partners[:3]

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
                            types, numbers, accounts, cards, currency="KGS", country="KG"):
        with transaction.atomic():
            point = Point(longitude, latitude)
            organization = Organization.objects.create(owner=owner, title=title, opens_at=opens_at, closes_at=closes_at,
                                                       description=description, image_id=image_id, address=address,
                                                       location=point, currency=currency, country=country)
            organization.types.set(types)
            for number in numbers:
                OrgPhoneNumberService.create(organization=organization, number=number)
            for link in accounts:
                OrgSocialNetworkContactService.create(organization=organization, url=link)

            DiscountCardService.bulk_create_discounts(cards=cards, organization=organization)

            return organization

    @classmethod
    def update(cls, organization, image_id, longitude, latitude, description, types,
               title, opens_at, closes_at, address, currency, show_contacts, country):
        try:
            point = Point(longitude, latitude)
            organization.image_id = image_id
            organization.location = point
            organization.title = title
            organization.opens_at = opens_at
            organization.closes_at = closes_at
            organization.address = address
            organization.currency = currency
            organization.show_contacts = show_contacts
            organization.country = country
            organization.description = description
            organization.types.set(types)
            organization.save()

            return organization

        except Exception as e:
            raise IntegrityException('Can not update organization: {e}'.format(e=str(e)))

    @classmethod
    def deactivate(cls, organization):
        try:
            organization.is_deleted = True
            organization.save()

            return organization

        except Exception as e:
            raise IntegrityException('Can not deactivate organization: {e}'.format(e=str(e)))


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
    def create(cls, *args, **kwargs):
        try:
            DiscountCard.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException('Duplicate cards are not allowed')

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
        with transaction.atomic():
            for card_data in cards:
                if card_data['type'] == DiscountCard.CUMULATIVE:
                    card_data['currency'] = organization.currency
                cls.create(organization=organization, **card_data)

    @classmethod
    def get_fixed_discounts_of_organization(cls, organization: Organization) -> QuerySet:
        return DiscountCard.objects.filter(organization=organization, type=DiscountCard.FIXED, is_published=True)


class CardOwnershipService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return CardOwnership.objects.get(*args, **kwargs)
        except CardOwnership.DoesNotExist:
            raise ObjectNotFoundException('CardOwner not found')

    @classmethod
    def filter(cls, *args, **kwargs):
        return CardOwnership.objects.filter(*args, **kwargs)

    @classmethod
    def get_client_cumulative_card(cls, client: User, organization: Organization) -> Union[DiscountCard, None]:
        ownership = cls.filter(user=client, card__organization=organization, card__type=DiscountCard.CUMULATIVE).first()
        if ownership:
            return ownership.card
        return None


class SubscriptionService:
    @classmethod
    def is_subscribed(cls, organization: Organization, user: User) -> bool:
        return Subscription.objects.filter(organization=organization, user=user).exists()

    @classmethod
    def get_number_of_subscriptions(cls, organization: Organization) -> int:
        return Subscription.objects.filter(organization=organization).count()

    @classmethod
    def toggle_subscription_status(cls, organization: Organization, user: User) -> bool:
        subscription, created = Subscription.objects.get_or_create(organization=organization, user=user)
        if created:
            return True
        subscription.delete()
        return False
