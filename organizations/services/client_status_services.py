from decimal import Decimal
from typing import Union

from django.db import transaction
from django.db.models import Sum, F
from django.db.models.functions import Coalesce

from organizations.models import OrganizationClientFinancialStatus, Organization, DiscountCard
from organizations.services.card_services import DiscountCardService
from organizations.services.cashback_group_services import CashbackGroupService
from organizations.services.cumulative_group_services import CumulativeGroupService
from transactions.models import Transaction
from users.models import User


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
    def get_client_cumulative_card(cls, client: User, organization: Organization) -> Union[DiscountCard, None]:
        ownership = cls.get(user=client, card__organization=organization, card__type=DiscountCard.CUMULATIVE)
        if ownership:
            return ownership.card
        return None

    @classmethod
    def get_client_financial_status_data(cls, client: User, organization: Organization) -> dict:
        from transactions.services.transaction_services import TransactionService
        user_totals = TransactionService.get_user_totals(client=client, organization=organization,
                                                         currency=organization.currency.code)

        total_spent_in_cumulative_group = TransactionService.get_client_total_spent_in_cumulative_group(
            client=client, organization=organization, currency=organization.currency.code
        )

        total_saved_in_organization = user_totals['total_savings'] + user_totals['total_from_cashback']
        cumulative_card = None
        next_level_limit = None
        accrued_cashback = cls.get_client_accrued_cashback(client=client, organization=organization)

        client_status = cls.get(user=client, organization=organization)
        if client_status is not None:
            if client_status.card is not None:
                cumulative_card = client_status.card.id
                next_level_limit = 0 if client_status.card.next_cumulative is None else client_status.card.next_cumulative.limit

        if next_level_limit is None:
            lowest_card = DiscountCardService.get_lowest_cumulative_card(organization=organization)
            next_level_limit = lowest_card.limit if lowest_card is not None else 0

        return {
            'active_card': cumulative_card,
            'total_spent': total_spent_in_cumulative_group,
            'total_saved': total_saved_in_organization,
            'next_limit': next_level_limit,
            'accrued_cashback': accrued_cashback,
        }

    @classmethod
    def update_client_cumulative_card(cls, client_status: OrganizationClientFinancialStatus):
        from transactions.services.transaction_services import TransactionService
        total_spent_in_cumulative_group = TransactionService.get_client_total_spent_in_cumulative_group(
            client=client_status.user,
            organization=client_status.organization,
            currency=client_status.organization.currency.code
        )

        highest_card_possible = DiscountCard.objects.filter(
            type=DiscountCard.CUMULATIVE, is_published=True, organization=client_status.organization,
            limit__lte=total_spent_in_cumulative_group
        ).order_by('-limit').first()

        client_status.card = highest_card_possible
        client_status.save(update_fields=('card',))

        # ToDo: Call this method asynchronously
        cls.update_cumulative_group_partner_cards(client=client_status.user,
                                                  organization=client_status.organization,
                                                  total_spent=total_spent_in_cumulative_group)

    @classmethod
    # ToDo: make this method asynchronous
    def update_cumulative_group_partner_cards(cls, client: User, organization: Organization, total_spent: Decimal):
        partner_ids = CumulativeGroupService.get_partners_in_same_cumulative_group(organization=organization)
        for partner_id in partner_ids:
            client_status = OrganizationClientFinancialStatusService.get_or_create(
                user=client, organization_id=partner_id
            )

            highest_card_possible = DiscountCard.objects.filter(
                type=DiscountCard.CUMULATIVE, is_published=True, organization_id=partner_id, limit__lte=total_spent
            ).order_by('-limit').first()

            client_status.card = highest_card_possible
            client_status.save(update_fields=('card',))

    @classmethod
    def can_use_given_card(cls, client: User, card: DiscountCard) -> bool:
        if not card.is_published:
            return False

        if card.type == DiscountCard.FIXED or card.type == DiscountCard.CASHBACK:
            return True

        if card is not None:
            owned_card = cls.get_client_cumulative_card(client=client, organization=card.organization)
            return card == owned_card

        return False

    @classmethod
    def has_enough_cashback_amount(cls, client: User, organization: Organization, amount: Decimal) -> bool:
        return cls.get_client_accrued_cashback(client=client, organization=organization) >= amount

    @classmethod
    def get_client_accrued_cashback(cls, client: User, organization: Organization) -> Decimal:
        partner_ids = CashbackGroupService.get_partners_in_same_cashback_group(organization=organization)
        partner_ids.append(organization.id)

        accrued_cashback = OrganizationClientFinancialStatus.objects.filter(
            user=client, organization__in=partner_ids).aggregate(total=Coalesce(Sum('accrued_cashback'), 0))

        return accrued_cashback['total']

    @classmethod
    @transaction.atomic
    def use_corporate_cashback(cls, client: User, organization: Organization, amount: Decimal):
        partner_ids = CashbackGroupService.get_partners_in_same_cashback_group(organization=organization)
        client_statuses = OrganizationClientFinancialStatus.objects.filter(
            user=client, organization__in=partner_ids).order_by('-accrued_cashback')

        for client_status in client_statuses:
            to_subtract = min(client_status.accrued_cashback, amount)
            client_status.accrued_cashback = F('accrued_cashback') - to_subtract
            client_status.save(update_fields=('accrued_cashback',))

            amount = amount - to_subtract
            if amount <= 0:
                break

    @classmethod
    def recalculate_cashback_after_refund(cls, client_status: OrganizationClientFinancialStatus,
                                          refunded_transaction: Transaction):
        cashback_change = refunded_transaction.from_cashback - refunded_transaction.to_cashback

        client_status.accrued_cashback = F('accrued_cashback') + cashback_change
        client_status.save(update_fields=('accrued_cashback',))
        client_status.refresh_from_db()
