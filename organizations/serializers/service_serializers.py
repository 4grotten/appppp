from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Organization
from organizations.models import Service
from organizations.serializers.categories_serializers import OrganizationTypeSerializer
from shop.models import ShopItem


class ServiceSerializer(serializers.ModelSerializer):
    icon = ImageSerializer()
    banner = ImageSerializer()

    class Meta:
        model = Service
        fields = ('id', 'is_discounts', 'is_entertainment', 'is_map', 'is_resume', 'is_wholesale', 'is_application',
                  'ordering', 'name', 'icon', 'banner', 'description')


class OrganizationServiceSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    time_working = serializers.SerializerMethodField(read_only=True)

    def get_time_working(self, organization: Organization):
        working_type = organization.time_working
        if working_type == 1:
            return 'around_the_clock'
        if working_type == 2:
            return 'open'
        if working_type == 3:
            return 'closed'

    class Meta:
        model = Organization
        fields = ('id', 'title', 'image', 'types', 'opens_at', 'closes_at', 'time_working',
                  'verification_status', 'avg_check', 'currency', 'full_location')
