from rest_framework import serializers

from organizations.models import Organization, OrganizationCategory
from users.models import User


class PartnerQueryParamSerializer(serializers.Serializer):
    partner = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True), default=None)


class OrganizationAndCategorySerializer(serializers.Serializer):
    category = serializers.PrimaryKeyRelatedField(queryset=OrganizationCategory.objects.all())
    partner = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True),
                                                 default=None)


class OrganizationTransactionsQueryParamSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    processed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)
    start = serializers.DateField(default=None)
    end = serializers.DateField(default=None)
    search = serializers.IntegerField(default=None)


class OrganizationQueryParamSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))


class OrganizationUserQueryParamSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))


class MonthYearQueryParamSerializer(serializers.Serializer):
    month_year = serializers.DateField(default=None, input_formats=["%Y-%m"])
