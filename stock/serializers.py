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
        fields = ('id', 'size', 'format_criteria')


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
        fields = ('id', 'organization', 'name', 'images', 'subcategory', 'price', 'discounted_price')


class ShopItemLinkSetSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    def get_name(self, stock: ShopItemLinksSetStock):
        return stock.shop_item.name

    def get_images(self, stock: ShopItemLinksSetStock):
        images = stock.shop_item.images.all()
        return ImageSerializer(images, many=True, context=self.context).data

    class Meta:
        model = ShopItemLinksSetStock
        fields = ('id', 'name', 'images', 'link')


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


class StockSetsSerializer(serializers.ModelSerializer):
    set_stock_count = serializers.SerializerMethodField()
    link_set_stock_count = serializers.SerializerMethodField()

    def get_set_stock_count(self, item: ShopItem):
        count = ShopItem.objects.filter(shop_items_set_stocks__main_shop_item=item).count()
        return count

    def get_link_set_stock_count(self, item: ShopItem):
        count = ShopItem.objects.filter(shop_items_link_set_stocks__main_shop_item=item).count()
        return count

    class Meta:
        model = ShopItem
        fields = ('set_stock_count', 'link_set_stock_count',)


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


class CreateAvailableSizesSerializer(serializers.Serializer):
    available_sizes = serializers.ListSerializer(child=serializers.IntegerField(), required=False, default=[])


class ShopItemsSetSerializer(serializers.Serializer):
    shop_items_set = serializers.ListSerializer(child=serializers.IntegerField(), required=False, default=[])


class ShopLinkItemsSetSerializer(serializers.Serializer):
    shop_items_link_set = serializers.ListSerializer(child=serializers.CharField(), required=False, default=[])
