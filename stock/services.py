from common.exceptions import ObjectNotFoundException
from shop.services.item_services import ShopItemService
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory, StockCart, ShopItemSizeCount


class StockService:

    @classmethod
    def get(cls, **filters):
        try:
            return StockCart.objects.get(**filters)
        except StockCart.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

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
    def add_size_quantity(cls, stock_cart: int, size_format: SizeFormat, quantity: int):
        size_format = SizeFormat.objects.get(id=size_format.id)
        stock_cart = StockCart.objects.get(id=stock_cart)
        item_size_quantity, created = ShopItemSizeCount.objects.get_or_create(size_format=size_format,
                                                                              stock_cart=stock_cart)
        item_size_quantity.quantity = quantity
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
