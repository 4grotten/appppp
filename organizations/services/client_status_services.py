from decimal import Decimal
from typing import Union

from organizations.models import OrganizationClientFinancialStatus, Organization, DiscountCard
from organizations.services.card_services import DiscountCardService
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

        total_spent_in_organization = user_totals['total_spent']
        total_saved_in_organization = user_totals['total_savings']
        cumulative_card = None
        next_level_limit = None

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
            'total_spent': total_spent_in_organization,
            'total_saved': total_saved_in_organization,
            'next_limit': next_level_limit
        }

    @classmethod
    def update_client_cumulative_card(cls, client_status: OrganizationClientFinancialStatus):
        from transactions.services.transaction_services import TransactionService
        user_totals = TransactionService.get_user_totals(client=client_status.user,
                                                         organization=client_status.organization,
                                                         currency=client_status.organization.currency.code)
        total_spent_in_organization = user_totals['total_spent']

        highest_card_possible = DiscountCard.objects.filter(
            type=DiscountCard.CUMULATIVE, is_published=True, organization=client_status.organization,
            limit__lte=total_spent_in_organization
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
        client_status = cls.get(user=client, organization=organization)
        if client_status is not None:
            return client_status.accrued_cashback >= amount
        return False

    @classmethod
    def get_client_accrued_cashback(cls, client: User, organization: Organization) -> Decimal:
        client_status = cls.get(user=client, organization=organization)
        if client_status is not None:
            return client_status.accrued_cashback
        return Decimal(0)
