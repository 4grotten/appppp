from datetime import timedelta
from decimal import Decimal
from typing import Union

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.db.models.functions import Coalesce

from common.exceptions import (
    NotAcceptableException, ObjectNotFoundException, IntegrityException,
    PermissionDeniedException
)
from organizations.models import Organization, DiscountCard
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.organization_services import OrganizationService
from transactions.models import Transaction
from transactions.services.stats_services import StatisticsService
from users.models import User


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
    def get_user_transaction_detail(cls, user: User, transaction_id: int):
        transaction_object = cls.get(id=transaction_id)

        if transaction_object.client != user:
            raise PermissionDeniedException('Permission denied')

        return transaction_object

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

    @classmethod
    def get_user_transaction_organizations(cls, client: User, start_date, end_date):
        if not start_date and not end_date:
            return cls.get_user_tr_organizations_without_date(client)
        return cls.get_user_tr_organizations_with_date(client=client, start_date=start_date, end_date=end_date)

    @staticmethod
    def get_user_tr_organizations_without_date(client):
        transactions = Transaction.objects.filter(client=client, is_processed=True)
        organizations = Organization.objects.filter(id__in=transactions.values('organization_id')).distinct()
        return organizations

    @staticmethod
    def get_user_tr_organizations_with_date(client, start_date, end_date):
        end_date = end_date + timedelta(days=1)
        transactions = Transaction.objects.filter(client=client, is_processed=True).filter(
            created_at__range=[start_date, end_date])
        organizations = Organization.objects.filter(id__in=transactions.values('organization_id')).distinct()
        return organizations

    @classmethod
    def get_user_totals(cls, client: User, currency: str, start_date=None, end_date=None):
        transactions = Transaction.objects.filter(client=client, is_processed=True)
        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(updated_at__range=[start_date, end_date])
        transactions = transactions.order_by().values('currency').annotate(total_spent=Coalesce(Sum('final_amount'), 0),
                                                                           total_savings=Coalesce(Sum('savings'), 0))
        return StatisticsService.get_stats_in_one_currency(totals=transactions, currency=currency)

    @classmethod
    def get_user_transactions(cls, client: User):
        transactions = Transaction.objects.filter(client=client, is_processed=True)
        return transactions
