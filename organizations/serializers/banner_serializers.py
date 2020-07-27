from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Banner, Organization


class BannerSerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = Banner
        fields = ('id', 'image', 'linked_organization',)


class OrganizationIDSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))


class BannerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ('host_organization', 'linked_organization', 'image',)
