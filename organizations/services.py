from decimal import Decimal
from itertools import groupby
from typing import Tuple, Union

from django.contrib.gis.geos import Point
from django.db import transaction, IntegrityError
from django.db.models import QuerySet, F

from common.exceptions import ObjectNotFoundException, NotAcceptableException, ValidationException, IntegrityException
from users.models import User
from .models import (
    DiscountCard, Organization, OrganizationClientFinancialStatus, Membership, PhoneNumber, SocialNetworkContact,
)


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
        partners = Organization.objects.filter(
            id__in=organization.requested_partnerships.filter(is_accepted=True).values_list('accepted_by', flat=True))

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
    @transaction.atomic
    def create_organization(cls, owner, title, description, image_id,
                            opens_at, closes_at, address, longitude, latitude,
                            types, numbers, accounts, cards, currency="KGS", country="KG"):
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
    def create_or_reactivate(cls, organization: Organization, percent: int, type: str, **kwargs):
        reactivated = DiscountCard.objects.filter(is_published=False, organization=organization,
                                                  percent=percent, type=type).update(is_published=True)
        if not reactivated:
            cls.create(organization=organization, percent=percent, type=type, **kwargs)

    @classmethod
    def get_grouped_discounts(cls, organization_id: int) -> dict:
        discounts = DiscountCard.objects.filter(organization_id=organization_id, is_published=True)
        discounts_dict = {
            DiscountCard.CUMULATIVE: [],
            DiscountCard.FIXED: []
        }

        for discount_type, group in groupby(discounts, lambda x: x.type):
            discounts_dict[discount_type] = list(group)

        return discounts_dict

    @classmethod
    def delete_discount(cls, discount: DiscountCard, user: User) -> DiscountCard:
        if not OrganizationService.user_can_edit_organization(organization_id=discount.organization.id, user=user):
            raise NotAcceptableException('No rights to edit organization')

        if not cls.is_card_editable(discount=discount):
            raise NotAcceptableException('Discount card can not be deleted')

        if discount.type == DiscountCard.FIXED:
            discount.is_published = False
            discount.save(update_fields=('is_published',))
            return discount

        discount.delete()

    @classmethod
    def update_discount(cls, discount: DiscountCard, user: User,
                        limit: Decimal = None, percent: int = None) -> DiscountCard:
        if not OrganizationService.user_can_edit_organization(organization_id=discount.organization.id, user=user):
            raise NotAcceptableException('No rights to edit organization')

        if not cls.is_card_editable(discount=discount):
            raise NotAcceptableException('Discount card can not be updated')

        if discount.type == DiscountCard.FIXED:
            discount = cls.swap_or_update(discount=discount, percent=percent)
            return discount

        if limit:
            discount.limit = limit
        if percent:
            discount.percent = percent
        try:
            discount.save()
        except IntegrityError:
            raise IntegrityException('Duplicate cards are not allowed')
        return discount

    @classmethod
    @transaction.atomic
    def swap_or_update(cls, discount: DiscountCard, percent: Union[int, None]):
        if not percent:
            raise IntegrityException('Percent is required for fixed discount')

        temp = 999
        updated = DiscountCard.objects.filter(is_published=False, percent=percent).update(percent=temp)

        if not updated:
            discount.percent = percent
            try:
                discount.save(update_fields=('percent',))
            except IntegrityError:
                raise IntegrityException('Duplicate cards are not allowed')
            return discount

        old_value = discount.percent
        discount.percent = percent
        discount.save()

        DiscountCard.objects.filter(is_published=False, percent=temp).update(percent=old_value)

    @classmethod
    def is_card_editable(cls, discount: DiscountCard) -> bool:
        if discount.type == DiscountCard.FIXED:
            return True
        return not discount.clients.exists()

    @classmethod
    @transaction.atomic
    def bulk_create_discounts(cls, cards: list, organization: Organization):
        should_organize = False

        for card_data in cards:
            if card_data['type'] == DiscountCard.CUMULATIVE:
                should_organize = True
                card_data['currency'] = organization.currency
                cls.create(organization=organization, **card_data)
            else:
                cls.create_or_reactivate(organization=organization, **card_data)

        if should_organize:
            cls.organize_cumulative_cards(organization=organization)

    @classmethod
    @transaction.atomic
    def organize_cumulative_cards(cls, organization: Organization):
        # reset existing "next_cumulative" pointers
        organization.discounts.filter(type=DiscountCard.CUMULATIVE).update(next_cumulative=None)

        cumulative_cards = organization.discounts.filter(
            is_published=True, type=DiscountCard.CUMULATIVE).order_by('limit')

        for i in range(len(cumulative_cards) - 1):
            cumulative_cards[i].next_cumulative = cumulative_cards[i + 1]
            cumulative_cards[i].save()

    @classmethod
    def get_fixed_discounts_of_organization(cls, organization: Organization) -> QuerySet:
        return DiscountCard.objects.filter(organization=organization, type=DiscountCard.FIXED, is_published=True)

    @classmethod
    def get_lowest_cumulative_card(cls, organization: Organization) -> Union[DiscountCard, None]:
        return organization.discounts.filter(type=DiscountCard.CUMULATIVE, is_published=True,
                                             previous_cumulative=None).order_by('limit').first()

    @classmethod
    @transaction.atomic
    def bulk_delete_discounts(cls, cards: list, organization: Organization, deleted_by: User):
        should_organize = False

        for card in cards:
            if not card.organization == organization:
                raise NotAcceptableException('Card does not belong to this organization')
            if not cls.is_card_editable(discount=card):
                raise NotAcceptableException('Card is not editable')
            if card.type == DiscountCard.CUMULATIVE:
                should_organize = True
            cls.delete_discount(discount=card, user=deleted_by)

        if should_organize:
            cls.organize_cumulative_cards(organization=organization)

    @classmethod
    @transaction.atomic
    def bulk_update_discounts(cls, cards_data: list, organization: Organization, updated_by: User):
        should_organize = False

        for card_data in cards_data:
            card = card_data.pop('id')

            if not card.organization == organization:
                raise NotAcceptableException('Card does not belong to this organization')
            if not cls.is_card_editable(discount=card):
                raise NotAcceptableException('Card is not editable')
            if card.type == DiscountCard.CUMULATIVE:
                should_organize = True

            cls.update_discount(discount=card, user=updated_by, **card_data)

        if should_organize:
            cls.organize_cumulative_cards(organization=organization)


class OrganizationClientFinancialStatusService:
    @classmethod
    def get(cls, *args, **kwargs) -> Union[OrganizationClientFinancialStatus, None]:
        try:
            return OrganizationClientFinancialStatus.objects.get(*args, **kwargs)
        except OrganizationClientFinancialStatus.DoesNotExist:
            return None

    @classmethod
    def filter(cls, *args, **kwargs):
        return OrganizationClientFinancialStatus.objects.filter(*args, **kwargs)

    @classmethod
    def get_or_create(cls, *args, **kwargs) -> OrganizationClientFinancialStatus:
        client_status, _ = OrganizationClientFinancialStatus.objects.get_or_create(*args, **kwargs)
        return client_status

    @classmethod
    def change_totals(cls, status: OrganizationClientFinancialStatus,
                      spent: Decimal, saved: Decimal) -> OrganizationClientFinancialStatus:
        try:
            status.total_spent = F('total_spent') + spent
            status.total_saved = F('total_saved') + saved
            status.save()
            status.refresh_from_db()
            return status
        except IntegrityError:
            raise IntegrityException('Could not change total spent')

    @classmethod
    def get_client_cumulative_card(cls, client: User, organization: Organization) -> Union[DiscountCard, None]:
        ownership = cls.get(user=client, card__organization=organization, card__type=DiscountCard.CUMULATIVE)
        if ownership:
            return ownership.card
        return None

    @classmethod
    def get_client_financial_status_data(cls, client: User, organization: Organization) -> dict:
        total_spent_in_organization = 0
        total_saved_in_organization = 0
        cumulative_card = None
        next_level_limit = None

        client_status = cls.get(user=client, organization=organization)
        if client_status is not None:
            total_spent_in_organization = client_status.total_spent
            total_saved_in_organization = client_status.total_saved

            if client_status.card is not None:
                cumulative_card = client_status.card.id
                next_level_limit = 0 if client_status.card.next_cumulative is None else client_status.card.next_cumulative.limit

        if next_level_limit is None:
            lowest_card = DiscountCardService.get_lowest_cumulative_card(organization=organization)
            next_level_limit = lowest_card.limit if lowest_card is not None else 0

        return {
            'active_card': cumulative_card,
            'total_spent': total_spent_in_organization,
            'total_saved': total_saved_in_organization,
            'next_limit': next_level_limit
        }

    @classmethod
    def update_client_cumulative_card(cls, client_status: OrganizationClientFinancialStatus):
        highest_card_possible = DiscountCard.objects.filter(
            type=DiscountCard.CUMULATIVE, is_published=True, organization=client_status.organization,
            limit__lte=client_status.total_spent
        ).order_by('-limit').first()

        if highest_card_possible is None:
            return

        client_status.card = highest_card_possible
        client_status.save(update_fields=('card',))

    @classmethod
    def can_use_given_card(cls, client: User, card: DiscountCard) -> bool:
        if not card.is_published:
            return False

        if card.type == DiscountCard.FIXED:
            return True

        if card is not None:
            owned_card = cls.get_client_cumulative_card(client=client, organization=card.organization)
            return card == owned_card

        return False
