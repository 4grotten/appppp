from django.utils import timezone
from rest_framework import serializers

from common.models import Country, City
from organizations.models import Organization, OrganizationCategory
from users.models import User


class PartnerQueryParamSerializer(serializers.Serializer):
    partner = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True), default=None)
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), default=None)
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), default=None)


class OrganizationAndCategorySerializer(serializers.Serializer):
    category = serializers.PrimaryKeyRelatedField(queryset=OrganizationCategory.objects.all())
    partner = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True),
                                                 default=None)
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), default=None)
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), default=None)


class OrganizationCoutrySerializer(serializers.Serializer):
    country = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), default=None)
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all(), default=None)
    current_timestamp_lt = serializers.DateTimeField(default=timezone.now())


class OrganizationTransactionsQueryParamSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    processed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)
    start = serializers.DateField(default=None)
    end = serializers.DateField(default=None)
    search = serializers.IntegerField(default=None)
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)


class OrganizationQueryParamSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))


class OptionalOrganizationQueryParamSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True),
                                                      default=None)


class OrganizationUserQueryParamSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))


class GlobalAttendanceQueryParamSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))


class MonthYearQueryParamSerializer(serializers.Serializer):
    month_year = serializers.DateField(default=None, input_formats=["%Y-%m"])
