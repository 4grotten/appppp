from datetime import timedelta
from decimal import Decimal
from typing import Union

from django.db import IntegrityError, transaction
from django.db.models import Sum, OuterRef, Subquery, F
from django.db.models.functions import Coalesce

from common.exceptions import (
    NotAcceptableException, ObjectNotFoundException, IntegrityException,
    PermissionDeniedException
)
from notifications.constants import (
    DISCOUNT_NOTIFICATION_MODE, ACCEPT_DISCOUNT_TYPE, DISCOUNT_COMPLETE_TITLE,
    DISCOUNT_COMPLETE_DESCRIPTION, DISCOUNT_COMPLETE_USER_TITLE, ACCEPT_SELLER_DISCOUNT_TYPE
)
from notifications.services import NotificationService
from organizations.models import Organization, DiscountCard
from organizations.services.client_status_services import OrganizationClientFinancialStatusService
from organizations.services.organization_services import OrganizationService
from notifications.tasks import sent_notification
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

        role = OrganizationService.get_user_role_in_organization(organization=organization, user=processed_by)

        instance = Transaction.objects.create(client=client, organization=organization, processed_by=processed_by,
                                              employee_name=processed_by.full_name, employee_role=role,
                                              employee_avatar=processed_by.avatar, currency=organization.currency)
        return instance

    @classmethod
    def get_transaction(cls, transaction_id: int, requested_by: User) -> Transaction:
        instance = cls.get(id=transaction_id, is_processed=True)

        if instance.client != requested_by and not OrganizationService.user_can_see_stats(
                organization=instance.organization, user=requested_by):
            raise PermissionDeniedException('Permission denied')

        return instance

    @classmethod
    @transaction.atomic
    def complete_transaction(cls,
                             transaction_id: int,
                             processed_by: User,
                             original_amount: Decimal,
                             discount_percent: int,
                             source_card: Union[DiscountCard, None],
                             from_cashback: Decimal,
                             ) -> Transaction:

        current_transaction = cls.get(id=transaction_id, processed_by=processed_by, is_processed=False)

        if source_card is not None and not OrganizationClientFinancialStatusService.can_use_given_card(
                client=current_transaction.client, card=source_card):
            raise NotAcceptableException('Client cannot use this card')

        cashback_percent = 0
        if source_card is not None and source_card.type == DiscountCard.CASHBACK:
            cashback_percent = discount_percent
            discount_percent = 0

        if from_cashback > 0 and not OrganizationClientFinancialStatusService.has_enough_cashback_amount(
                client=current_transaction.client, organization=current_transaction.organization, amount=from_cashback):
            raise NotAcceptableException('Not enough accrued cashback amount')

        try:
            current_transaction.original_amount = original_amount
            current_transaction.savings = (original_amount * discount_percent) / 100
            current_transaction.discount_percent = max(discount_percent, cashback_percent)
            current_transaction.from_cashback = from_cashback
            current_transaction.source_card = source_card
            current_transaction.is_processed = True
            if source_card is not None:
                current_transaction.discount_type = source_card.type
            current_transaction.save()

            sent_notification.delay(
                recipient_id=current_transaction.client_id,
                sender_id=current_transaction.processed_by_id,
                mode=DISCOUNT_NOTIFICATION_MODE,
                notification_type=ACCEPT_DISCOUNT_TYPE,
                title=DISCOUNT_COMPLETE_USER_TITLE.format(discount_percent=str(current_transaction.discount_percent)),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id)
            )
            sent_notification.delay(
                recipient_id=current_transaction.processed_by_id,
                sender_id=current_transaction.client_id,
                mode=DISCOUNT_NOTIFICATION_MODE,
                notification_type=ACCEPT_SELLER_DISCOUNT_TYPE,
                title=DISCOUNT_COMPLETE_TITLE.format(discount_percent=str(current_transaction.discount_percent)),
                description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=str(current_transaction.final_amount),
                                                                 currency=current_transaction.currency.code),
                organization_id=current_transaction.organization_id,
                extra_data=dict(transaction_id=current_transaction.id)
            )
        except IntegrityError:
            raise IntegrityException('Could not complete transaction')

        client_status = OrganizationClientFinancialStatusService.get_or_create(
            user=current_transaction.client,
            organization=current_transaction.organization
        )
        OrganizationClientFinancialStatusService.update_client_cumulative_card(client_status=client_status)

        if source_card is not None and source_card.type == DiscountCard.CASHBACK:
            cashback = current_transaction.final_amount * cashback_percent / 100
            client_status.accrued_cashback = F('accrued_cashback') + cashback
            client_status.save(update_fields=('accrued_cashback',))
            client_status.refresh_from_db()
            # ToDo: send notification about adding to cashback

        if from_cashback > 0:
            client_status.accrued_cashback = F('accrued_cashback') - from_cashback
            client_status.save(update_fields=('accrued_cashback',))
            client_status.refresh_from_db()
            # ToDo: send notification about taking from cashback

        return current_transaction

    @classmethod
    def get_user_transaction_organizations(cls, client: User, start_date, end_date):
        transactions = Transaction.objects.filter(client=client, is_processed=True)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(created_at__range=[start_date, end_date])

        organizations = Organization.objects.filter(id__in=transactions.values('organization_id')).annotate(
            latest_transaction_time=Subquery(
                Transaction.objects.filter(organization=OuterRef('pk'), client=client, is_processed=True
                                           ).order_by('-updated_at').values('updated_at')[:1]
            )
        ).order_by('-latest_transaction_time')
        return organizations

    @classmethod
    def get_user_totals(cls, client: User, currency: str,
                        organization: Organization = None, start_date=None, end_date=None) -> dict:
        transactions = Transaction.objects.filter(client=client, is_processed=True)

        if organization is not None:
            transactions = transactions.filter(organization=organization)

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

    @classmethod
    def get_organization_transactions(cls, organization: Organization, processed_by: User = None,
                                      start_date=None, end_date=None, search_id: int = None):

        transactions = Transaction.objects.filter(organization=organization, is_processed=True)

        if processed_by is not None:
            transactions = transactions.filter(processed_by=processed_by)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(updated_at__range=[start_date, end_date])

        if search_id is not None:
            transactions = transactions.filter(id__contains=search_id)

        return transactions
