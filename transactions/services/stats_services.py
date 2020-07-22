from datetime import timedelta

from django.db.models import Sum
from django.db.models.functions import Coalesce

from common.exceptions import NotAcceptableException
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from transactions.models import Transaction
from users.models import User


class StatisticsService:
    @classmethod
    def get_total_stats_of_partners(cls, organization: Organization, requesting_user: User, start_day, end_day) -> dict:
        if not OrganizationService.user_can_see_stats(organization=organization, user=requesting_user):
            raise NotAcceptableException('No rights to see stats of organization')

        partners = organization.requested_partnerships.filter(is_accepted=True).values('accepted_by')
        end_day = end_day + timedelta(days=1)
        transactions = Transaction.objects.filter(updated_at__range=[start_day, end_day]).filter(
            is_processed=True).filter(organization__in=partners
                                      ).aggregate(total_spent=Coalesce(Sum('final_amount'), 0),
                                                  total_savings=Coalesce(Sum('savings'), 0))

        # ToDo: calculate currencies
        return transactions
