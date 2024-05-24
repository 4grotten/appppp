from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import ImageSerializer
from organizations.models import HotlinkCollectionSubcategory
from organizations.services.organization_services import OrganizationService
from shop.models import ItemCategory, ItemSubcategory
from shop.services.category_services import ItemSubcategoryService
from stock.serializers import CriteriaSubcategorySerializer


class ItemSubcategoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization', 'category')

    def validate(self, attrs):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException(_('No rights to edit organization'))

        return attrs


class ItemSubcategoryBriefSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, subcategory: ItemSubcategory):
        return ImageSerializer(
            subcategory.category.icon, context=self.context).data if subcategory.category.icon else None

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'icon')


class ItemSubcategorySerializer(ItemSubcategoryBriefSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    criteria_subcategory = CriteriaSubcategorySerializer(many=True, required=False)

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization', 'icon', 'criteria_subcategory',)

class NonEmptyItemSubcategorySerializer(ItemSubcategoryBriefSerializer):
    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name',)


class ItemSubcategoryForHotlinksSerializer(ItemSubcategoryBriefSerializer):
    category_name = serializers.CharField(source='category.name')
    is_selected = serializers.SerializerMethodField()

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'category_name', 'is_selected', 'icon')

    def get_is_selected(self, subcategory: ItemSubcategory) -> bool:
        if 'hotlink' not in self.context:
            return False
        return HotlinkCollectionSubcategory.objects.filter(
            hotlink=self.context['hotlink'], subcategory=subcategory).exists()


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


