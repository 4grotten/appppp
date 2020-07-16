from typing import Union

from django.db import IntegrityError
from django.db.models import Sum
from django.db.models.functions import Coalesce

from common.exceptions import NotAcceptableException, ObjectNotFoundException, IntegrityException
from organizations.models import Organization, DiscountCard
from organizations.services import OrganizationService, OrganizationClientFinancialStatusService
from users.models import User
from .models import Transaction


class TransactionService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Transaction.objects.get(**kwargs)
        except Transaction.DoesNotExist:
            raise ObjectNotFoundException('Transaction not found')

    @classmethod
    def preprocess_transaction(cls, client: User, organization: Organization, processed_by: User) -> Transaction:
        if not OrganizationService.user_can_sell(organization=organization, user=processed_by):
            raise NotAcceptableException('No rights to sell in this organization')

        transaction = Transaction.objects.create(client=client, organization=organization, processed_by=processed_by,
                                                 currency=organization.currency)
        return transaction

    @classmethod
    def complete_transaction(cls,
                             transaction_id: int,
                             processed_by: User,
                             original_amount,
                             savings,
                             discount_percent: int,
                             source_card: Union[DiscountCard, None]
                             ) -> Transaction:

        transaction = cls.get(id=transaction_id, processed_by=processed_by, is_processed=False)

        if source_card is not None and not OrganizationClientFinancialStatusService.can_use_given_card(
                client=transaction.client, card=source_card):
            raise NotAcceptableException('Client cannot use this card')

        try:
            transaction.original_amount = original_amount
            transaction.savings = savings
            transaction.discount_percent = discount_percent
            transaction.source_card = source_card
            transaction.is_processed = True
            if source_card is not None:
                transaction.discount_type = source_card.type
            transaction.save()

        except IntegrityError:
            raise IntegrityException('Could not complete transaction')

        return transaction

    @classmethod
    def get_total_saved_amount(cls, client: User, organization: Organization):
        aggregated = Transaction.objects.filter(
            client=client, organization=organization, is_processed=True).aggregate(total=Coalesce(Sum('savings'), 0))
        return aggregated['total']
