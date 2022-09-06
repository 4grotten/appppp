from django.db.models import Sum
from rest_framework import serializers

from common.serializers import ImageSerializer
from shop.models import ShopItem, ItemSubcategory, CartItem
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory, ShopItemLinksSetStock, ShopItemSizeCount


class CriteriaSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CriteriaSubcategory
        fields = ('id', 'name',)


class FormatCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatCriteria
        fields = ('id', 'name',)


class OnlySizeFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeFormat
        fields = ('id', 'size',)


class SizeFormatSerializer(serializers.ModelSerializer):
    format_criteria = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()

    def get_icon(self, size_format: SizeFormat):
        icon = CriteriaSubcategory.objects.get(format_criteria=size_format.format_criteria)
        return ImageSerializer(icon.icon, context=self.context).data if icon else None

    def get_format_criteria(self, size_format: SizeFormat):
        return size_format.format_criteria.name

    class Meta:
        model = SizeFormat
        fields = ('id', 'size', 'format_criteria', 'icon')


class SizeFormatByItemSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()
    format_criteria = serializers.SerializerMethodField()

    def get_format_criteria(self, size_format: SizeFormat):
        return size_format.format_criteria.name

    def get_count(self, size_format: SizeFormat):
        user = self.context['request'].user
        item = self.context['shop_item']
        cart_item = CartItem.objects.filter(item=item, cart__user=user, cart__is_open=True, size=size_format).first()
        current_count_in_cart = cart_item.count if cart_item else 0
        try:
            size_count = ShopItemSizeCount.objects.get(size=size_format, main_shop_item=item).count - current_count_in_cart
        except:
            size_count = None
        return size_count

    class Meta:
        model = SizeFormat
        fields = ('id', 'size', 'count', 'format_criteria')


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


class OrganizationShopItemsInSetSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)
    subcategory = SubcategorySerializer()
    in_set = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()

    def get_currency(self, item: ShopItem):
        return str(item.organization.currency)

    def get_in_set(self, item: ShopItem):
        main_shop_item = ShopItem.objects.get(id=self.context['main_shop_item_id'])
        stock_items = ShopItem.objects.filter(shop_items_set_stocks__main_shop_item=main_shop_item)
        if item in stock_items:
            return True
        return False

    class Meta:
        model = ShopItem
        fields = ('id', 'organization', 'currency', 'name', 'images', 'subcategory', 'price', 'discounted_price', 'in_set')


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


class ShopItemSetIdsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = ('id',)


class ShopItemSizeCountSetSerializer(serializers.ModelSerializer):
    size = SizeFormatSerializer()

    class Meta:
        model = ShopItemSizeCount
        fields = ('id', 'size', 'count')


class ShopItemSizeCountSerializer(serializers.ModelSerializer):
    size = SizeFormatSerializer(required=False, default=None)
    count = serializers.SerializerMethodField()

    def get_count(self, size_count: ShopItemSizeCount):
        user = self.context['request'].user
        item = self.context['shop_item']
        cart_item = CartItem.objects.filter(item=item, cart__user=user, cart__is_open=True, size=None).first()
        current_count_in_cart = cart_item.count if cart_item else 0
        try:
            size_count = size_count.count - current_count_in_cart
        except:
            size_count = None
        return size_count

    class Meta:
        model = ShopItemSizeCount
        fields = ('size', 'count')


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
    available_sizes = serializers.SerializerMethodField()

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

    def get_available_sizes(self, item: ShopItem):
        queryset = item.available_sizes.all().order_by('order')
        return SizeFormatSerializer(queryset, many=True).data


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


class OrganizationSubcategorySerializer(serializers.ModelSerializer):
    icon = serializers.SerializerMethodField()

    def get_icon(self, subcategory: ItemSubcategory):
        return ImageSerializer(
            subcategory.category.icon, context=self.context).data if subcategory.category.icon else None

    class Meta:
        model = ItemSubcategory
        fields = ('id', 'name', 'icon')