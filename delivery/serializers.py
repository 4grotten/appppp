from rest_framework import serializers

from common.serializers import CountrySerializer, CitySerializer
from delivery.models import DeliveryInfo
from organizations.serializers.organization_serializers import OrganizationDetailedSerializer
from shop.models import Cart
from shop.serializers.cart_serializers import CartListSerializer
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
                  'phone', 'comment', 'status',
                  'longitude', 'latitude',
                  'full_location',
                  'who_pays', 'amount', 'currency'
                  )


class CartListWithDeliveryInfoSerializer(CartListSerializer):
    transaction = TransactionDetailSerializer()

    class Meta:
        fields = ('id', 'items_count', 'totals', 'organization', 'images', 'transaction')
        model = Cart


# class DeliveryTakeSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DeliveryInfo
#         fields = ('delivery_organization_id',)
