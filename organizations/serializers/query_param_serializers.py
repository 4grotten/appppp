from rest_framework import serializers

from common.models import Country, City
from organizations.models import Organization, OrganizationCategory
from shop.models import ItemSubcategory
from transactions.models import Transaction, PayoutSystem
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
    subcategory = serializers.PrimaryKeyRelatedField(queryset=ItemSubcategory.objects.all(), default=None)


class OrganizationMapsLocationSerializer(serializers.Serializer):
    longitude = serializers.FloatField(allow_null=True)
    latitude = serializers.FloatField(allow_null=True)
    zoom = serializers.IntegerField()


class OrganizationTransactionsQueryParamSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    processed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)
    start = serializers.DateField(default=None)
    end = serializers.DateField(default=None)
    search = serializers.IntegerField(default=None)
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)
    payout_system = serializers.PrimaryKeyRelatedField(queryset=PayoutSystem.objects.all(), default=None)
    status = serializers.ChoiceField(choices=Transaction.STATUS, default=None)
    withdrawal_type = serializers.ChoiceField(choices=Transaction.WITHDRAWAL_TYPES, default=None)


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
