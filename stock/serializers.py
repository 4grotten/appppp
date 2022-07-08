from rest_framework import serializers

from common.serializers import ImageSerializer
from shop.models import ShopItem, ItemSubcategory
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory, ShopItemLinksSetStock, ShopItemSizeCount


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


class ShopItemsAvailableSizesSerializer(serializers.ModelSerializer):
    available_sizes = SizeFormatSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = ('id', 'name', 'available_sizes',)


class ShopItemShortSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = ('id', 'name', 'images')


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name')


class ShopItemSetSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)
    subcategory = SubcategorySerializer()

    class Meta:
        model = ShopItem
        fields = ('id', 'name', 'images', 'subcategory')


class ShopItemLinkSetSerializer(serializers.ModelSerializer):
    shop_item = ShopItemShortSerializer()

    class Meta:
        model = ShopItemLinksSetStock
        fields = ('id', 'shop_item', 'link')


class LinkStockSerializer(serializers.Serializer):
    link = serializers.CharField()


class ShopItemSizeCountSetSerializer(serializers.ModelSerializer):
    size = SizeFormatSerializer()

    class Meta:
        model = ShopItemSizeCount
        fields = ('id', 'size', 'count')

class AddShopItemSizeCountSetSerializer(serializers.ModelSerializer):

    class Meta:
        model = ShopItemSizeCount
        fields = ('size', 'count')


# class FillStockCollectionBySizaSerializer(serializers.Serializer):
#     available_sizes = serializers.ListSerializer(child=serializers.IntegerField(), required=False, default=[])


# class StockCartSerializer(serializers.ModelSerializer):
#     available_size = SizeFormatSerializer(many=True)
#
#     class Meta:
#         model = StockCart
#         fields = ('id', 'shop_item', 'available_size')
#
#
# class AddSizeQuantitySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ShopItemSizeCount
#         fields = ('id', 'size_format', 'quantity')

#
# class ShopItemCollectionsSerializer(serializers.ModelSerializer):
#     images = ImageSerializer(many=True)
#
#     class Meta:
#         model = ShopItem
#         fields = ('id', 'name', 'images', 'subcategory', 'price',)


# class ShopItemLinkForCollectionSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ShopItemLinkForCollection
#         fields = '__all__'

#
class CreateAvailableSizesSerializer(serializers.Serializer):
    available_sizes = serializers.ListSerializer(child=serializers.IntegerField(), required=False, default=[])


class ShopItemsSetSerializer(serializers.Serializer):
    shop_items_set = serializers.ListSerializer(child=serializers.IntegerField(), required=False, default=[])
    shop_items_link_set = serializers.ListSerializer(child=serializers.CharField(), required=False, default=[])
#
# class CreateLinkCollectionsSerializer(serializers.Serializer):
#     related_item_links = serializers.ListSerializer(child=serializers.CharField(), required=False, default=[])

# class CollectionsSerializer(serializers.ModelSerializer):
#     related_items = ShopItemCollectionsSerializer(many=True)
#
#     class Meta:
#         model = ShopItemSizeCount
#         fields = ('id', 'related_items')
