from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Banner
from organizations.serializers.organization_serializers import OrganizationTitleImageSerializer


class BannerSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    linked_organization = OrganizationTitleImageSerializer()

    class Meta:
        model = Banner
        fields = ('id', 'image', 'linked_organization',)


class BannerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ('host_organization', 'linked_organization', 'image',)


class BannerUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ('image', 'linked_organization')
