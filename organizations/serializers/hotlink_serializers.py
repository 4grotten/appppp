from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.constants import (
    HOTLINK_COLLECTION, HOTLINK_URL, HOTLINK_URL_ITEM, HOTLINK_URL_ORGANIZATION, HOTLINK_URL_EXTERNAL, HOTLINK_PARTNERS
)
from organizations.models import Hotlink, HotlinkCollectionLink
from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
from organizations.services.hotlink_services import HotlinkService
from organizations.services.partnership_services import PartnershipService
from shop.models import ItemSubcategory, ShopItem
from shop.serializers.item_serializers import ItemInHotlinkSerializer


class HotlinkSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    #Fixme: return this after mobile app release
    # link_type = serializers.SerializerMethodField()
    linked_organization = OrganizationWithTypeImageSerializer()
    linked_item = ItemInHotlinkSerializer()
    image = ImageSerializer()
    partners_count = serializers.SerializerMethodField()

    def get_title(self, hotlink: Hotlink) -> str:
        return HotlinkService.get_hotlink_title(hotlink=hotlink)

    # Fixme: return this after mobile app release
    # def get_link_type(self, hotlink: Hotlink) -> str:
    #     if not hotlink.link_type == HOTLINK_URL:
    #         return hotlink.link_type
    #     if hotlink.linked_item:
    #         return HOTLINK_URL_ITEM
    #     if hotlink.linked_organization:
    #         return HOTLINK_URL_ORGANIZATION
    #     return HOTLINK_URL_EXTERNAL
    def get_partners_count(self, hotlink: Hotlink) -> int:
        if hotlink.link_type == HOTLINK_PARTNERS:
            return PartnershipService.get_organization_partners(hotlink.linked_organization).count()
        return 0

    class Meta:
        model = Hotlink
        fields = (
            'id', 'title', 'content', 'link_type', 'linked_organization', 'linked_item', 'image',
            'partners_count'
        )


class HotlinkWithCountsSerializer(HotlinkSerializer):
    items_count = serializers.SerializerMethodField()
    links_count = serializers.SerializerMethodField()
    subcategories_count = serializers.SerializerMethodField()
    collection_items = serializers.SlugRelatedField(many=True, read_only=True, slug_field='item_id')
    collection_links = serializers.SlugRelatedField(many=True, read_only=True, slug_field='content')
    collection_subcategories = serializers.SlugRelatedField(many=True, read_only=True, slug_field='subcategory_id')

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
            'collection_items', 'collection_links', 'collection_subcategories'
        )


class HotlinkCreateSerializer(serializers.ModelSerializer):
    collection_items = serializers.PrimaryKeyRelatedField(
        queryset=ShopItem.objects.all(), many=True, required=False, default=[]
    )
    collection_links = serializers.ListSerializer(child=serializers.CharField(), required=False, default=[])
    collection_subcategories = serializers.PrimaryKeyRelatedField(
        queryset=ItemSubcategory.objects.all(), many=True, required=False, default=[]
    )

    class Meta:
        model = Hotlink
        fields = (
            'organization', 'content', 'link_type', 'image', 'collection_items', 'collection_links',
            'collection_subcategories'
        )


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
