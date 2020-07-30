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
    def get_total_stats_of_partners(cls, organization: Organization, requesting_user: User, start_day, end_day,
                                    currency: str) -> dict:
        if not OrganizationService.user_can_see_stats(organization=organization, user=requesting_user):
            raise NotAcceptableException('No rights to see stats of organization')

        partners = organization.requested_partnerships.filter(is_accepted=True).values('accepted_by')
        end_day = end_day + timedelta(days=1)
        transactions = Transaction.objects.filter(
            updated_at__range=[start_day, end_day]
        ).filter(
            is_processed=True
        ).filter(
            organization__in=partners
        ).order_by().values('currency').annotate(total_spent=Coalesce(Sum('final_amount'), 0),
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
