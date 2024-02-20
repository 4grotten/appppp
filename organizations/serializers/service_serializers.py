from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Organization
from organizations.models import Service
from organizations.serializers.categories_serializers import OrganizationTypeSerializer
from shop.models import ShopItem


class ServiceSerializer(serializers.ModelSerializer):
    icon = ImageSerializer()

    class Meta:
        model = Service
        fields = ('id', 'is_discounts', 'is_entertainment', 'is_map', 'is_resume', 'ordering', 'name', 'icon',)


class OrganizationServiceSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    shop_items = serializers.SerializerMethodField()
    time_working = serializers.SerializerMethodField(read_only=True)

    def get_time_working(self, organization: Organization):
        working_type = organization.time_working
        if working_type == 1:
            return 'around_the_clock'
        if working_type == 2:
            return 'open'
        if working_type == 3:
            return 'closed'

    def get_shop_items(self, organization: Organization):
        items = ShopItem.objects.filter(price__isnull=False,
                                        images__isnull=False, organization=organization).order_by('-updated_at')[:3]
        images = []
        for item in items:
            photo = item.images.last()
            if photo not in images:
                images.append(photo)
        return {
            'images': ImageSerializer(images, many=True, context={'request': self.context.get('request')}).data
        }

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'types', 'opens_at', 'closes_at', 'shop_items', 'time_working',
                  'verification_status', 'avg_check', 'currency')
