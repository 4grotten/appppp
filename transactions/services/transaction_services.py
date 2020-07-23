from decimal import Decimal
from typing import Union

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce

from common.exceptions import NotAcceptableException, ObjectNotFoundException, IntegrityException
from organizations.models import Organization, DiscountCard
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.organization_services import OrganizationService
from users.models import User
from transactions.models import Transaction


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
    @transaction.atomic
    def complete_transaction(cls,
                             transaction_id: int,
                             processed_by: User,
                             original_amount: Decimal,
                             discount_percent: int,
                             source_card: Union[DiscountCard, None]
                             ) -> Transaction:

        current_transaction = cls.get(id=transaction_id, processed_by=processed_by, is_processed=False)

        if source_card is not None and not OrganizationClientFinancialStatusService.can_use_given_card(
                client=current_transaction.client, card=source_card):
            raise NotAcceptableException('Client cannot use this card')

        try:
            current_transaction.original_amount = original_amount
            current_transaction.savings = (original_amount * discount_percent) / 100
            current_transaction.discount_percent = discount_percent
            current_transaction.source_card = source_card
            current_transaction.is_processed = True
            if source_card is not None:
                current_transaction.discount_type = source_card.type
            current_transaction.save()
        except IntegrityError:
            raise IntegrityException('Could not complete transaction')

        client_status = OrganizationClientFinancialStatusService.get_or_create(
            user=current_transaction.client,
            organization=current_transaction.organization
        )
        client_status = OrganizationClientFinancialStatusService.change_totals(
            status=client_status,
            spent=current_transaction.final_amount,
            saved=current_transaction.savings
        )
        OrganizationClientFinancialStatusService.update_client_cumulative_card(client_status=client_status)

        return current_transaction

    @classmethod
    def get_total_saved_amount(cls, client: User, organization: Organization):
        aggregated = Transaction.objects.filter(
            client=client, organization=organization, is_processed=True).aggregate(total=Coalesce(Sum('savings'), 0))
        return aggregated['total']
