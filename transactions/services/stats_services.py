from datetime import timedelta

from django.db.models import Sum, QuerySet
from django.db.models.functions import Coalesce

from common.exceptions import NotAcceptableException
from common.services.currency import CurrencyConverterService
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from transactions.models import Transaction
from users.models import User


class StatisticsService:
    @classmethod
    def get_totals_of_organization(cls, organization: Organization, start_date=None, end_date=None,
                                   processed_by: User = None) -> dict:
        transactions = Transaction.objects.filter(is_processed=True, organization=organization)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(updated_at__range=[start_date, end_date])

        if processed_by is not None:
            transactions = transactions.filter(processed_by=processed_by)

        transactions = transactions.order_by().values('currency').annotate(total_spent=Coalesce(Sum('final_amount'), 0),
                                                                           total_savings=Coalesce(Sum('savings'), 0))

        return cls.get_stats_in_one_currency(totals=transactions, currency=organization.currency.code)

    @classmethod
    def get_total_stats_of_partners(cls, organization: Organization, requesting_user: User, currency: str,
                                    start_date=None, end_date=None) -> dict:
        if not OrganizationService.user_can_see_stats(organization=organization, user=requesting_user):
            raise NotAcceptableException('No rights to see stats of organization')

        partners = organization.requested_partnerships.filter(is_accepted=True).values('accepted_by')
        transactions = Transaction.objects.filter(is_processed=True).filter(organization__in=partners)

        if start_date is not None and end_date is not None:
            end_date = end_date + timedelta(days=1)
            transactions = transactions.filter(updated_at__range=[start_date, end_date])

        transactions = transactions.order_by().values('currency').annotate(total_spent=Coalesce(Sum('final_amount'), 0),
                                                                           total_savings=Coalesce(Sum('savings'), 0))

        return cls.get_stats_in_one_currency(totals=transactions, currency=currency)

    @staticmethod
    def get_stats_in_one_currency(totals: QuerySet, currency: str) -> dict:
        """
        "totals" queryset should look like this
        QuerySet [{'currency': 'USD', 'total_spent': Decimal('80400.00'), 'total_savings': Decimal('20100.00')},
                  {'currency': 'KGS', 'total_spent': Decimal('10000.00'), 'total_savings': Decimal('0.00')}
                 ]
        """
        total_spent = 0
        total_savings = 0

        for transaction in totals:
            if transaction['currency'] == currency:
                total_spent += transaction['total_spent']
                total_savings += transaction['total_savings']
                continue
            total_spent += CurrencyConverterService.convert(from_currency=transaction['currency'],
                                                            to_currency=currency, amount=transaction['total_spent'])
            total_savings += CurrencyConverterService.convert(from_currency=transaction['currency'],
                                                              to_currency=currency, amount=transaction['total_savings'])

        return {
            'total_spent': total_spent,
            'total_savings': total_savings,
            'currency': currency
        }

    @staticmethod
    def get_transaction_totals_in_one_currency(totals: QuerySet, currency: str) -> dict:
        """
        "totals" queryset should look like this
        QuerySet [
            {
                'currency': 'USD', 'total_spent': Decimal('7320.80'),
                'total_savings': Decimal('85.00'),
                'total_from_cashback': Decimal('494.20')
            },
            {
                'currency': 'KGS', 'total_spent': Decimal('10000.00'),
                'total_savings': Decimal('0.00'),
                'total_from_cashback': Decimal('494.20')
            }
        ]
        """

        total_spent = 0
        total_savings = 0
        total_from_cashback = 0

        for currency_transaction in totals:
            if currency_transaction['currency'] == currency:
                total_spent += currency_transaction['total_spent']
                total_savings += currency_transaction['total_savings']
                total_from_cashback += currency_transaction['total_from_cashback']
                continue
            total_spent += CurrencyConverterService.convert(
                from_currency=currency_transaction['currency'], to_currency=currency,
                amount=currency_transaction['total_spent']
            )
            total_savings += CurrencyConverterService.convert(
                from_currency=currency_transaction['currency'], to_currency=currency,
                amount=currency_transaction['total_savings']
            )
            total_from_cashback += CurrencyConverterService.convert(
                from_currency=currency_transaction['currency'], to_currency=currency,
                amount=currency_transaction['total_from_cashback']
            )

        return {
            'total_spent': total_spent,
            'total_savings': total_savings,
            'total_from_cashback': total_from_cashback,
            'currency': currency
        }
