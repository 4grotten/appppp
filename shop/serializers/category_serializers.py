from django.db.models import Q
import logging
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.models import File
from common.serializers import ImageSerializer
from organizations.models import HotlinkCollectionSubcategory
from organizations.services.organization_services import OrganizationService
from shop.models import ItemCategory, ItemSubcategory
from shop.services.category_services import ItemSubcategoryService
from stock.serializers import CriteriaSubcategorySerializer


logger = logging.getLogger(__name__)


class ItemSubcategoryCreateSerializer(serializers.ModelSerializer):
    sub_icon_data = serializers.SerializerMethodField()

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization', 'category', 'sub_icon', 'sub_icon_data')

    def get_sub_icon_data(self, subcategory: ItemSubcategory):
        if subcategory.sub_icon:
            return ImageSerializer(subcategory.sub_icon, context=self.context).data
        return None

    def validate(self, attrs):
        user = self.context['request'].user
        organization = attrs.get('organization')
        if organization and not OrganizationService.user_can_edit_organization(user=user, organization=organization):
            raise NotAcceptableException(_('No rights to edit organization'))
        return attrs


class ItemSubcategoryBriefSerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()
    sub_icon = serializers.SerializerMethodField()

    def get_icon(self, subcategory: ItemSubcategory):
        icon_obj = subcategory.sub_icon or (subcategory.category.icon if subcategory.category else None)
        
        if icon_obj:
            return ImageSerializer(icon_obj, context=self.context).data
        return None

    def get_sub_icon(self, subcategory: ItemSubcategory):
        if subcategory.sub_icon:
            return ImageSerializer(subcategory.sub_icon, context=self.context).data
        return None
    
    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'icon', 'sub_icon')



class ItemSubcategorySerializer(ItemSubcategoryBriefSerializer):
    organization = serializers.PrimaryKeyRelatedField(read_only=True)
    criteria_subcategory = CriteriaSubcategorySerializer(many=True, required=False)
    sub_icon = serializers.SerializerMethodField()

    def get_sub_icon(self, subcategory: ItemSubcategory):
        if subcategory.sub_icon:
            return ImageSerializer(subcategory.sub_icon, context=self.context).data
        return None

    def update(self, instance, validated_data):
        sub_icon_data = self.initial_data.get("sub_icon", serializers.empty)
        request = self.context.get("request")
        user_id = getattr(getattr(request, "user", None), "id", None)

        logger.info(
            "[ItemSubcategorySerializer.update] start subcategory_id=%s user_id=%s sub_icon_input=%s validated_keys=%s",
            instance.id,
            user_id,
            sub_icon_data,
            list(validated_data.keys()),
        )
        print(
            f"[ItemSubcategorySerializer.update] start subcategory_id={instance.id} "
            f"user_id={user_id} sub_icon_input={sub_icon_data}"
        )

        if sub_icon_data is not serializers.empty:
            if sub_icon_data in (None, ""):
                instance.sub_icon = None
                logger.info(
                    "[ItemSubcategorySerializer.update] clear sub_icon for subcategory_id=%s",
                    instance.id,
                )
                print(f"[ItemSubcategorySerializer.update] clear sub_icon subcategory_id={instance.id}")
            else:
                try:
                    instance.sub_icon = File.objects.get(pk=int(sub_icon_data))
                    logger.info(
                        "[ItemSubcategorySerializer.update] set sub_icon=%s for subcategory_id=%s",
                        instance.sub_icon_id,
                        instance.id,
                    )
                    print(
                        f"[ItemSubcategorySerializer.update] set sub_icon={instance.sub_icon_id} "
                        f"subcategory_id={instance.id}"
                    )
                except (TypeError, ValueError):
                    logger.warning(
                        "[ItemSubcategorySerializer.update] invalid sub_icon value=%s for subcategory_id=%s",
                        sub_icon_data,
                        instance.id,
                    )
                    print(
                        f"[ItemSubcategorySerializer.update] invalid sub_icon={sub_icon_data} "
                        f"subcategory_id={instance.id}"
                    )
                    raise serializers.ValidationError({"sub_icon": _("A valid integer is required.")})
                except File.DoesNotExist:
                    logger.warning(
                        "[ItemSubcategorySerializer.update] sub_icon file not found value=%s subcategory_id=%s",
                        sub_icon_data,
                        instance.id,
                    )
                    print(
                        f"[ItemSubcategorySerializer.update] file not found sub_icon={sub_icon_data} "
                        f"subcategory_id={instance.id}"
                    )
                    raise serializers.ValidationError({"sub_icon": _("File does not exist.")})

        updated_instance = super().update(instance, validated_data)
        logger.info(
            "[ItemSubcategorySerializer.update] success subcategory_id=%s sub_icon_id=%s",
            updated_instance.id,
            updated_instance.sub_icon_id,
        )
        print(
            f"[ItemSubcategorySerializer.update] success subcategory_id={updated_instance.id} "
            f"sub_icon_id={updated_instance.sub_icon_id}"
        )
        return updated_instance

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'organization', 'icon', 'sub_icon', 'criteria_subcategory')

       
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
        icon_to_show = subcategory.sub_icon or subcategory.category.icon
        
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


