from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Organization
from organizations.models import Service
from organizations.serializers.categories_serializers import OrganizationTypeSerializer
from shop.models import ShopItem
from shop.serializers.item_serializers import ItemsSerializer


class ServiceSerializer(serializers.ModelSerializer):
    icon = ImageSerializer()

    class Meta:
        model = Service
        fields = ('id', 'name', 'icon',)


class OrganizationServiceSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    shop_items = serializers.SerializerMethodField()

    def get_shop_items(self, organization: Organization):
        queryset = ShopItem.objects.filter(price__isnull=False, organization=organization).order_by('-updated_at')[:3]
        return {
            'items': ItemsSerializer(queryset, many=True, context={'request': self.context.get('request')}).data
        }

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'types', 'opens_at', 'closes_at', 'shop_items',)