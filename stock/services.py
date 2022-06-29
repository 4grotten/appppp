from transliterate.utils import _

from common.exceptions import ObjectNotFoundException
from shop.models import ShopItem
from shop.services.item_services import ShopItemService
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory, StockCart, ShopItemSizeCount, \
    ShopItemCollections, ShopItemLinkForCollection


class StockService:

    @classmethod
    def get(cls, **filters):
        try:
            return StockCart.objects.get(**filters)
        except StockCart.DoesNotExist:
            raise ObjectNotFoundException(_('Stock cart not found'))

    @classmethod
    def get_size_format(cls, **filters):
        try:
            return SizeFormat.objects.get(**filters)
        except SizeFormat.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

    @classmethod
    def create_stock_cart(cls, shop_item_id: int, avaliable_sizes: list):
        shop_item = ShopItemService.get(id=shop_item_id)

        avaliable_sizes_list = []
        for i in avaliable_sizes:
            avaliable_sizes_list.append(cls.get_size_format(id=i))
        stock_cart, created = StockCart.objects.get_or_create(shop_item=shop_item)

        if created:
            stock_cart.available_size.add(*avaliable_sizes_list)
        else:
            stock_cart.available_size.clear()
            stock_cart.available_size.add(*avaliable_sizes_list)

        return stock_cart

    @classmethod
    def create_shop_item_collection(cls, main_item: int, related_items=None, related_item_links=None):
        try:
            main_item = ShopItem.objects.get(id=main_item)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))


        shop_item_collection, created = ShopItemCollections.objects.get_or_create(main_item=main_item)

        related_items_list = []

        if related_item_links:
            for i in related_item_links:
                shop_item_link = ShopItemLinkForCollection.objects.create(link=i)
                related_items_list.append(shop_item_link)

            if created:
                shop_item_collection.related_item_links.add(*related_items_list)
            else:
                shop_item_collection.related_item_links.clear()
                shop_item_collection.related_item_links.add(*related_items_list)

        if related_items:
            for i in related_items:
                related_items_list.append(ShopItemService.get(id=i))

            if created:
                shop_item_collection.related_items.add(*related_items_list)
            else:
                shop_item_collection.related_items.clear()
                shop_item_collection.related_items.add(*related_items_list)

        return shop_item_collection


    @classmethod
    def add_size_quantity(cls, stock_cart_id: int, size_format: SizeFormat, quantity: int):
        try:
            size_format = SizeFormat.objects.get(id=size_format.id)
            stock_cart = StockCart.objects.get(id=stock_cart_id)
        except StockCart.DoesNotExist:
            raise ObjectNotFoundException(_('StockCart or SizeFormat not found'))
        item_size_quantity, created = ShopItemSizeCount.objects.get_or_create(size_format=size_format,
                                                                              stock_cart=stock_cart)
        item_size_quantity.quantity = quantity
        item_size_quantity.save()
        return item_size_quantity

    @classmethod
    def get_criteria_by_subcategory_id(cls, subcategory_id):
        return CriteriaSubcategory.objects.filter(
            item_subcategories__id=subcategory_id)

    @classmethod
    def get_format_by_criteria_subcategory_id(cls, criteria_subcategory_id):
        return FormatCriteria.objects.filter(
            criteria_subcategories__id=criteria_subcategory_id)

    @classmethod
    def get_sizes_by_format_id(cls, format_criteria_id):
        return SizeFormat.objects.select_related('format_criteria').filter(
            format_criteria__id=format_criteria_id).order_by('order')

    @classmethod
    def remove_shop_item_stock_cart(cls, stock_id):
        shop_item_stock_cart = cls.get(id=stock_id)
        return shop_item_stock_cart.delete()


    @classmethod
    def remove_shop_item_size_quantity(cls, item_size_quantity_id):
        try:
            item_size_quantity = ShopItemSizeCount.objects.get(id=item_size_quantity_id)
            return item_size_quantity.delete()
        except ShopItemSizeCount.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItemSizeCount not found'))

