from decimal import Decimal
from itertools import groupby
from typing import Union

from django.db import IntegrityError, transaction
from django.db.models import QuerySet, F
from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException, IntegrityException, NotAcceptableException
from common.services.currency import CurrencyConverterService
from notifications.constants import (
    NEW_DISCOUNT_TYPE, NEW_DISCOUNT_TITLE, NEW_DISCOUNT_DESCRIPTION, SYSTEM_NOTIFICATION_MODE, NEW_CASHBACK_TITLE,
    NEW_CASHBACK
)
from notifications.tasks import send_notifications_to_all_users
from organizations.models import DiscountCard, Organization
from organizations.services.organization_services import OrganizationService
from users.models import User


class DiscountCardService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return DiscountCard.objects.get(*args, **kwargs)
        except DiscountCard.DoesNotExist:
            raise ObjectNotFoundException(_('Discount not found'))

    @classmethod
    def create(cls, *args, **kwargs):
        try:
            DiscountCard.objects.create(*args, **kwargs)
        except IntegrityError:
            raise IntegrityException(_('Duplicate cards are not allowed'))

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
            DiscountCard.FIXED: [],
            DiscountCard.CASHBACK: []
        }

        for discount_type, group in groupby(discounts, lambda x: x.type):
            discounts_dict[discount_type] = list(group)

        return discounts_dict

    @classmethod
    def delete_discount(cls, discount: DiscountCard, user: User) -> DiscountCard:
        if not OrganizationService.user_can_edit_organization(organization=discount.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        if not cls.is_card_editable(discount=discount):
            raise NotAcceptableException(_('Discount card can not be deleted'))

        if discount.type == DiscountCard.FIXED:
            discount.is_published = False
            discount.save(update_fields=('is_published',))
            return discount

        discount.delete()

    @classmethod
    def update_discount(cls, discount: DiscountCard, user: User,
                        limit: Decimal = None, percent: int = None) -> DiscountCard:
        if not OrganizationService.user_can_edit_organization(organization=discount.organization, user=user):
            raise NotAcceptableException(_('No rights to edit organization'))

        if not cls.is_card_editable(discount=discount):
            raise NotAcceptableException(_('Discount card can not be updated'))

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
            raise IntegrityException(_('Duplicate cards are not allowed'))
        return discount

    @classmethod
    @transaction.atomic
    def swap_or_update(cls, discount: DiscountCard, percent: Union[int, None]):
        if not percent:
            raise IntegrityException(_('Percent is required for fixed discount'))

        temp = 999
        updated = DiscountCard.objects.filter(is_published=False, percent=percent).update(percent=temp)

        if not updated:
            discount.percent = percent
            try:
                discount.save(update_fields=('percent',))
            except IntegrityError:
                raise IntegrityException(_('Duplicate cards are not allowed'))
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
        percents = list()
        cashbacks = list()

        for card_data in cards:
            if card_data['type'] == DiscountCard.CASHBACK:
                cashbacks.append(card_data['percent'])
            else:
                percents.append(card_data['percent'])
            if card_data['type'] == DiscountCard.CUMULATIVE:
                should_organize = True
                card_data['currency'] = organization.currency
                cls.create(organization=organization, **card_data)
            else:
                cls.create_or_reactivate(organization=organization, **card_data)

        if should_organize:
            cls.organize_cumulative_cards(organization=organization)

        percents.sort()
        cashbacks.sort()
        not_dup_cashbacks = list(dict.fromkeys(cashbacks))
        not_dup_percents = list(dict.fromkeys(percents))
        str_percent = ', '.join(map(str, not_dup_percents))
        str_cashback = ', '.join(map(str, not_dup_cashbacks))
        if percents:
            transaction.on_commit(lambda: send_notifications_to_all_users.delay(
                organization_id=organization.id,
                mode=SYSTEM_NOTIFICATION_MODE,
                notification_type=NEW_DISCOUNT_TYPE,
                title=NEW_DISCOUNT_TITLE.format(percent=str_percent),
                description=NEW_DISCOUNT_DESCRIPTION.format(address=organization.address),
                extra_data=dict(percent=str_percent, address=organization.address)
            ))
        if cashbacks:
            transaction.on_commit(lambda: send_notifications_to_all_users.delay(
                organization_id=organization.id,
                mode=SYSTEM_NOTIFICATION_MODE,
                notification_type=NEW_CASHBACK,
                title=NEW_CASHBACK_TITLE.format(percent=str_cashback),
                description=NEW_DISCOUNT_DESCRIPTION.format(address=organization.address),
                extra_data=dict(cashback=str_cashback, address=organization.address)
            ))

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
    def get_cashback_discounts_of_organization(cls, organization: Organization) -> QuerySet:
        return DiscountCard.objects.filter(organization=organization, type=DiscountCard.CASHBACK, is_published=True)

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
                raise NotAcceptableException(_('Card does not belong to this organization'))
            if not cls.is_card_editable(discount=card):
                raise NotAcceptableException(_('Card is not editable'))
            if card.type == DiscountCard.CUMULATIVE:
                should_organize = True
            cls.delete_discount(discount=card, user=deleted_by)

        if should_organize:
            cls.organize_cumulative_cards(organization=organization)

    @classmethod
    @transaction.atomic
    def bulk_update_discounts(cls, cards_data: list, organization: Organization, updated_by: User):
        should_organize = False
        percents = list()
        cashbacks = list()

        for card_data in cards_data:
            card = card_data.pop('id')
            if not card.organization == organization:
                raise NotAcceptableException(_('Card does not belong to this organization'))
            if not cls.is_card_editable(discount=card):
                raise NotAcceptableException(_('Card is not editable'))
            if card.type == DiscountCard.CUMULATIVE:
                should_organize = True

            cls.update_discount(discount=card, user=updated_by, **card_data)

            if card.type == DiscountCard.CASHBACK:
                cashbacks.append(card_data['percent'])
            else:
                percents.append(card_data['percent'])

        if should_organize:
            cls.organize_cumulative_cards(organization=organization)

        percents.sort()
        cashbacks.sort()
        not_dup_cashbacks = list(dict.fromkeys(cashbacks))
        not_dup_percents = list(dict.fromkeys(percents))
        str_percent = ', '.join(map(str, not_dup_percents))
        str_cashback = ', '.join(map(str, not_dup_cashbacks))
        if percents:
            transaction.on_commit(lambda: send_notifications_to_all_users.delay(
                sender_id=updated_by.id,
                organization_id=organization.id,
                mode=SYSTEM_NOTIFICATION_MODE,
                notification_type=NEW_DISCOUNT_TYPE,
                title=NEW_DISCOUNT_TITLE.format(percent=str_percent),
                description=NEW_DISCOUNT_DESCRIPTION.format(address=organization.address)
            ))
        if cashbacks:
            transaction.on_commit(lambda: send_notifications_to_all_users.delay(
                sender_id=updated_by.id,
                organization_id=organization.id,
                mode=SYSTEM_NOTIFICATION_MODE,
                notification_type=NEW_DISCOUNT_TYPE,
                title=NEW_CASHBACK_TITLE.format(percent=str_cashback),
                description=NEW_DISCOUNT_DESCRIPTION.format(address=organization.address)
            ))

    @classmethod
    def get_unique_discount_percents_to_display(cls, organization: Organization) -> list:
        values = DiscountCard.objects.filter(
            is_published=True, organization=organization
        ).distinct('percent').order_by('percent').values_list('percent', flat=True)
        return values

    @classmethod
    def get_max_discount(cls, organization: Organization) -> int:
        max_discount = DiscountCard.objects.filter(
            is_published=True, organization=organization
        ).distinct('percent').order_by('-percent').values_list('percent', flat=True)[:1]
        if max_discount:
            return max_discount[0]
        return 0

    @classmethod
    def update_discount_currency(cls, organization: Organization, new_currency: str):
        rate = CurrencyConverterService.get_rate(from_currency=organization.currency.code, to_currency=new_currency)
        DiscountCard.objects.filter(organization=organization, type=DiscountCard.CUMULATIVE
                                    ).update(currency=new_currency, limit=F('limit') * rate)
