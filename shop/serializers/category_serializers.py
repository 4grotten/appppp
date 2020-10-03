from django.db.models import Q
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from organizations.services.organization_services import OrganizationService
from shop.models import ItemCategory, ItemSubcategory


class ItemCategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization', 'category')

    def validate(self, attrs):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException('No rights to edit organization')

        return attrs


class ItemCategorySerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization',)


class MainCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()

    def get_subcategories(self, main_category: ItemCategory) -> dict:
        organization = self.context['organization']
        if organization is None:
            subcategories = main_category.subcategories.filter(organization__isnull=True)
        else:
            subcategories = main_category.subcategories.filter(
                Q(organization__isnull=True) | Q(organization=organization))
        return ItemCategorySerializer(subcategories, many=True).data

    class Meta:
        model = ItemCategory
        fields = ('id', 'name', 'subcategories')
