from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.serializers.organization_serializers import OrganizationShortInfoSerializer
from shop.models import ShopItem
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory, StockCart, ShopItemSizeCount, \
    ShopItemLinkForCollection


class CriteriaSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CriteriaSubcategory
        fields = ('id', 'name',)


class FormatCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatCriteria
        fields = ('id', 'name',)


class SizeFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeFormat
        fields = ('id', 'size',)


class CreateStokeCartSerializer(serializers.Serializer):
    available_size = serializers.ListSerializer(child=serializers.IntegerField(), required=False, default=[])


class StockCartSerializer(serializers.ModelSerializer):
    available_size = SizeFormatSerializer(many=True)

    class Meta:
        model = StockCart
        fields = ('id', 'shop_item', 'available_size')


class AddSizeQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItemSizeCount
        fields = ('id', 'size_format', 'quantity')


class ShopItemCollectionsSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = ('id', 'name', 'images', 'subcategory', 'price', )


class ShopItemLinkForCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItemLinkForCollection
        fields = '__all__'


class CreateCollectionsSerializer(serializers.Serializer):
    related_items = serializers.ListSerializer(child=serializers.IntegerField(), required=False, default=[])


class CreateLinkCollectionsSerializer(serializers.Serializer):
    related_item_links = serializers.ListSerializer(child=serializers.CharField(), required=False, default=[])


class CollectionsSerializer(serializers.ModelSerializer):
    related_items = ShopItemCollectionsSerializer(many=True)

    class Meta:
        model = ShopItemSizeCount
        fields = ('id', 'related_items')


class LinkCollectionsSerializer(serializers.ModelSerializer):
    related_item_links = ShopItemLinkForCollectionSerializer(many=True)

    class Meta:
        model = ShopItemSizeCount
        fields = ('id', 'related_item_links')



