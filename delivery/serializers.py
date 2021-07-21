from rest_framework import serializers

from common.serializers import CountrySerializer, CitySerializer
from delivery.models import DeliveryInfo
from organizations.serializers.organization_serializers import OrganizationDetailedSerializer
from transactions.serializers.transaction_serializers import TransactionDetailSerializer


class DeliveryAllItemsCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()


class DeliveryInfoListSerializer(serializers.ModelSerializer):
    transaction = TransactionDetailSerializer()
    delivery_organization = OrganizationDetailedSerializer()
    country = CountrySerializer()
    city = CitySerializer()
    longitude = serializers.FloatField(allow_null=True, default=None, write_only=True)
    latitude = serializers.FloatField(allow_null=True, default=None, write_only=True)

    class Meta:
        model = DeliveryInfo
        fields = ('id', 'delivery_organization', 'country', 'city', 'transaction',
                  'address', 'apartment', 'intercom', 'entrance', 'floor',
                  'phone', 'comment', 'status', 'longitude',
                  'latitude',
                  'full_location',)
