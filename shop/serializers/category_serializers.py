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
        fields = ('id', 'name', 'organization', 'category', 'sub_icon')

    def validate(self, attrs):
        user = self.context['request'].user
        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException(_('No rights to edit organization'))

        return attrs


class ItemSubcategoryBriefSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, subcategory: ItemSubcategory):
        if subcategory.icon:
            return ImageSerializer(subcategory.sub_icon, context=self.context).data

        if subcategory.category and subcategory.category.icon:
            return ImageSerializer(subcategory.category.icon, context=self.context).data
            
        return None
    
    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'sub_icon')


class ItemSubcategorySerializer(ItemSubcategoryBriefSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    criteria_subcategory = CriteriaSubcategorySerializer(many=True, required=False)

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization', 'sub_icon', 'criteria_subcategory',)

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
    

class ItemSubcategory2Serializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, subcategory: ItemSubcategory):
        icon_to_show = subcategory.icon or subcategory.category.icon
        
        if icon_to_show:
            return ImageSerializer(icon_to_show, context=self.context).data
        return None


    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'icon')

class ItemCategorySerializer(serializers.ModelSerializer):
    icon = ImageSerializer()
    current_subcategory = serializers.SerializerMethodField()

    class Meta:
        model = ItemCategory
        fields = ('id', 'name', 'icon', 'current_subcategory')

    def get_current_subcategory(self, obj):
        selected_subcategory = self.context.get('selected_subcategory')
        if selected_subcategory and selected_subcategory.category_id == obj.id:
            return ItemSubcategory2Serializer(selected_subcategory).data
        return None

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
        return ItemSubcategorySerializer(subcategories, many=True, context=self.context).data
    
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
        return ItemSubcategorySerializer(subcategories, many=True, context=self.context).data

    class Meta:
        model = ItemCategory
        fields = ('id', 'icon', 'name', 'subcategories')


