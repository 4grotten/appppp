from django.db.models import Q
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import ImageSerializer
from organizations.services.organization_services import OrganizationService
from shop.models import ItemCategory, ItemSubcategory
from shop.services.category_services import ItemSubcategoryService


class ItemSubcategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization', 'category')

    def validate(self, attrs):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException('No rights to edit organization')

        return attrs


class ItemSubcategorySerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    icon = serializers.SerializerMethodField()

    def get_icon(self, subcategory: ItemSubcategory):
        return ImageSerializer(subcategory.category.icon).data if subcategory.category.icon else None

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization', 'icon')


class ItemSubcategoryBriefSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, subcategory: ItemSubcategory):
        return ImageSerializer(subcategory.category.icon).data if subcategory.category.icon else None

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'icon')


class ItemCategorySerializer(serializers.ModelSerializer):
    icon = ImageSerializer()

    class Meta:
        model = ItemCategory
        fields = ('id', 'name', 'icon')


class ItemCategoryWithSubcategoriesSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    icon = ImageSerializer()

    def get_subcategories(self, main_category: ItemCategory) -> dict:
        organization = self.context.get('organization', None)
        if organization is None:
            subcategories = main_category.subcategories.filter(organization__isnull=True)
        else:
            subcategories = main_category.subcategories.filter(
                Q(organization__isnull=True) | Q(organization=organization))
        return ItemSubcategorySerializer(subcategories, many=True).data

    class Meta:
        model = ItemCategory
        fields = ('id', 'name', 'icon', 'subcategories')


class ItemCategoryWithNonEmptySubcategoriesSerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    icon = ImageSerializer()

    def get_subcategories(self, main_category: ItemCategory) -> dict:
        subcategories = ItemSubcategoryService.get_general_nonempty_subcategories_in_category(
            category=main_category, country=self.context['country'], city=self.context['city']
        )
        return ItemSubcategorySerializer(subcategories, many=True).data

    class Meta:
        model = ItemCategory
        fields = ('id', 'icon', 'name', 'subcategories')
