from rest_framework import serializers

from common.serializers import FileSerializer
from .models import Organization, OrganizationType
from .services import OrganizationService


class OrganizationSerializer(serializers.ModelSerializer):
    image = FileSerializer(many=False)
    role = serializers.SerializerMethodField()
    types = serializers.StringRelatedField(many=True)

    def get_role(self, organization: Organization):
        user = self.context['request'].user
        return OrganizationService.get_user_role_in_organization(organization=organization, user=user)

    class Meta:
        model = Organization
        fields = ('title', 'image', 'role', 'description', 'image_id',
                  'opens_at', 'closes_at', 'show_contacts', 'types')


class OrganizationListSerializer(serializers.ModelSerializer):
    image = FileSerializer(many=False)
    role = serializers.SerializerMethodField()

    def get_role(self, organization: Organization):
        user = self.context['request'].user
        return OrganizationService.get_user_role_in_organization(organization=organization, user=user)

    class Meta:
        model = Organization
        fields = ('title', 'image', 'role')


class OrganizationCreateSerializer(serializers.ModelSerializer):
    description = serializers.CharField(required=True, allow_blank=False)
    image_id = serializers.IntegerField()

    class Meta:
        model = Organization
        fields = ('title', 'description', 'image_id', 'opens_at', 'closes_at', 'show_contacts', 'types')

    def validate(self, attrs):
        attrs['owner'] = self.context['request'].user
        return attrs


class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = ('id', 'title',)
