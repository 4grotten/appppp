from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.constants import HOTLINK_COLLECTION
from organizations.models import Hotlink, HotlinkCollectionLink
from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
from organizations.services.hotlink_services import HotlinkService
from shop.models import ItemSubcategory, ShopItem
from shop.serializers.item_serializers import ItemInHotlinkSerializer


class HotlinkSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()
    links_count = serializers.SerializerMethodField()
    subcategories_count = serializers.SerializerMethodField()
    linked_organization = OrganizationWithTypeImageSerializer()
    linked_item = ItemInHotlinkSerializer()
    image = ImageSerializer()

    def get_title(self, hotlink: Hotlink) -> str:
        return HotlinkService.get_hotlink_title(hotlink=hotlink)

    def get_items_count(self, hotlink: Hotlink) -> int:
        if hotlink.link_type == HOTLINK_COLLECTION:
            return hotlink.collection_items.count()
        return 0

    def get_links_count(self, hotlink: Hotlink) -> int:
        if hotlink.link_type == HOTLINK_COLLECTION:
            return hotlink.collection_links.count()
        return 0

    def get_subcategories_count(self, hotlink: Hotlink) -> int:
        if hotlink.link_type == HOTLINK_COLLECTION:
            return hotlink.collection_subcategories.count()
        return 0

    class Meta:
        model = Hotlink
        fields = (
            'id', 'title', 'content', 'link_type', 'items_count', 'links_count', 'subcategories_count',
            'linked_organization', 'linked_item', 'image',
        )


class HotlinkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotlink
        fields = ('organization', 'content', 'link_type', 'image',)


class HotlinkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotlink
        fields = ('content', 'link_type', 'image',)


class HotlinkItemsEditSerializer(serializers.Serializer):
    added = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all(), many=True)
    removed = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all(), many=True)


class HotlinkSubcategoriesEditSerializer(serializers.Serializer):
    added = serializers.PrimaryKeyRelatedField(queryset=ItemSubcategory.objects.all(), many=True)
    removed = serializers.PrimaryKeyRelatedField(queryset=ItemSubcategory.objects.all(), many=True)


class HotlinkCollectionLinkSerializer(serializers.ModelSerializer):
    hotlink = serializers.PrimaryKeyRelatedField(queryset=Hotlink.objects.all(), write_only=True)

    class Meta:
        model = HotlinkCollectionLink
        fields = ('id', 'hotlink', 'content')


class HotlinkCollectionLinkUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = HotlinkCollectionLink
        fields = ('content',)
