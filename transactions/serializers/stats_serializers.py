from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Organization
from organizations.services.organization_services import OrganizationService
from transactions.models import Balance
from transactions.services.stats_services import StatisticsService
from users.models import User
from users.serializers import UserWhitClientOrRoleInfoSerializer


class StartEndDateSerializer(serializers.Serializer):
    start = serializers.DateField(default=None)
    end = serializers.DateField(default=None)


class StartEndProcessedByQueryParamSerializer(serializers.Serializer):
    start = serializers.DateField(default=None)
    end = serializers.DateField(default=None)
    processed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)


class TotalStatsSerializer(serializers.Serializer):
    total_spent = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_savings = serializers.DecimalField(max_digits=16, decimal_places=2)
    currency = serializers.CharField()


class TotalAcceptedWithdrawalStatsSerializer(serializers.Serializer):
    total_withdrawal = serializers.DecimalField(max_digits=16, decimal_places=2)
    currency = serializers.CharField()


class BalanceTotalStatsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Balance
        fields = ('id', 'currency', 'balance_amount')


class OrganizationCalendarSerializer(serializers.Serializer):
    month_year = serializers.DateField(default=None, input_formats=["%Y-%m"])
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=True)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), required=True)


class CalendarClientSerializer(serializers.Serializer):
    client = serializers.SerializerMethodField()
    calendar = serializers.SerializerMethodField()

    def get_client(self, user: User):
        return UserWhitClientOrRoleInfoSerializer(user, context=self.context).data

    def get_calendar(self, user: User):
        return StatisticsService.get_days_when_client_did_transactions(organization=self.context['organization'],
                                                                       client=user,
                                                                       month_year=self.context['month_year'])

    class Meta:
        model = User
        fields = ('client', 'calendar')
