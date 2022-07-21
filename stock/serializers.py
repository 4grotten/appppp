from django.db.models import Sum
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


class StockSerializer(serializers.ModelSerializer):
    item_quantity = serializers.SerializerMethodField()
    criteria_subcategory = serializers.SerializerMethodField()
    collection_items_quantity = serializers.SerializerMethodField()
    available_sizes = SizeFormatSerializer(many=True)

    def get_criteria_subcategory(self, item: ShopItem):
        criteria_subcategory = CriteriaSubcategory.objects.filter(item_subcategories=item.subcategory).exists()
        if criteria_subcategory:
            criteria_subcategory = CriteriaSubcategory.objects.get(item_subcategories=item.subcategory)
            icon = ImageSerializer(
                criteria_subcategory.icon, context=self.context).data if criteria_subcategory.icon else None
            return {
                'id': criteria_subcategory.id,
                'name': criteria_subcategory.name,
                'icon': icon,
            }
        return None

    def get_item_quantity(self, item: ShopItem):
        count = ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total']
        if count and count > 0:
            return True
        return False

    def get_collection_items_quantity(self, item: ShopItem):
        item_set_quantity = ShopItem.objects.filter(shop_items_set_stocks__main_shop_item=item).count()
        item_set_links_quantity = ShopItem.objects.filter(shop_items_link_set_stocks__main_shop_item=item).count()
        return item_set_quantity + item_set_links_quantity

    class Meta:
        model = ShopItem
        fields = ('criteria_subcategory', 'available_sizes', 'collection_items_quantity', 'item_quantity')


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
