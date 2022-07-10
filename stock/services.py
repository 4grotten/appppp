import re

from django.db.models import Q
from transliterate.utils import _

from imports.admin import User
from organizations.models import Organization
from shop.models import ShopItem
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory, ShopItemSetStock, ShopItemLinksSetStock, \
    ShopItemSizeCount
from transactions.models import Transaction
from transliterate.utils import _

from common.exceptions import ObjectNotFoundException
from shop.models import ShopItem
from shop.services.item_services import ShopItemService
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory


# , StockCart, ShopItemSizeCount, \
# ShopItemCollections, ShopItemLinkForCollection


class StockService:

    # @classmethod
    # def get(cls, **filters):
    #     try:
    #         return StockCart.objects.get(**filters)
    #     except StockCart.DoesNotExist:
    #         raise ObjectNotFoundException(_('Stock cart not found'))

    @classmethod
    def get_size_format(cls, **filters):
        try:
            return SizeFormat.objects.get(**filters)
        except SizeFormat.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

    # @classmethod
    # def create_stock_cart(cls, shop_item_id: int, avaliable_sizes: list):
    #     shop_item = ShopItemService.get(id=shop_item_id)
    #
    #     avaliable_sizes_list = []
    #     for i in avaliable_sizes:
    #         avaliable_sizes_list.append(cls.get_size_format(id=i))
    #     stock_cart, created = StockCart.objects.get_or_create(shop_item=shop_item)
    #
    #     if created:
    #         stock_cart.available_size.add(*avaliable_sizes_list)
    #     else:
    #         stock_cart.available_size.clear()
    #         stock_cart.available_size.add(*avaliable_sizes_list)

    # return stock_cart
    # shop_item_id = [int(s) for s in re.findall(r'\b\d+\b', item_link)]
    @classmethod
    def add_shop_items_sets_in_stock(cls, main_item: int, shop_items=None):
        shop_item_stock, _ = ShopItemSetStock.objects.get_or_create(main_shop_item=main_item)
        shop_items_list = []
        if shop_items:
            for i in shop_items:
                shop_item = ShopItemService.get(id=i)
                shop_items_list.append(shop_item)
        shop_item_stock.shop_item.clear()
        shop_item_stock.shop_item.add(*shop_items_list)

    @classmethod
    def add_shop_items_links_sets_in_stock(cls, main_item, shop_item_links=None):
        # shop_item_stock, _ = ShopItemLinksSetStock.objects.get_or_create(shop_item=main_item)
        if shop_item_links:
            for link in shop_item_links:
                shop_item_by_link = [int(s) for s in re.findall(r'\b\d+\b', link)]
                shop_item = ShopItemService.get(id=shop_item_by_link[0])
                ShopItemLinksSetStock.objects.get_or_create(main_shop_item=main_item, shop_item=shop_item, link=link)

    @classmethod
    def add_shop_items_sets(cls, main_item: int, shop_items=None, shop_item_links=None):
        try:
            main_item = ShopItem.objects.get(id=main_item)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))
        if shop_items:
            cls.add_shop_items_sets_in_stock(main_item=main_item, shop_items=shop_items)
        if shop_item_links:
            cls.add_shop_items_links_sets_in_stock(main_item=main_item, shop_item_links=shop_item_links)

    @classmethod
    def add_shop_items_size_count(cls, main_item, size=None, count=None):
        shop_item = ShopItemService.get(id=main_item)
        shop_item_size_count, _ = ShopItemSizeCount.objects.get_or_create(main_shop_item=shop_item, size=size)
        shop_item_size_count.count = count
        shop_item_size_count.save()
        return shop_item_size_count

    @classmethod
    def get_not_choosen_size(cls, main_item):
        main_shop_item = ShopItemService.get(id=main_item)
        size_count = ShopItemSizeCount.objects.filter(main_shop_item=main_shop_item)
        array = []
        for i in size_count:
            array.append(i.size)
        array_result = []
        for i in main_shop_item.available_sizes.all():
            if i not in array:
                array_result.append(i)
        return array_result

    @classmethod
    def add_available_sizes(cls, shop_item_id: int, available_sizes=None):
        try:
            shop_item = ShopItem.objects.get(id=shop_item_id)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))

        available_sizes_list = []

        for i in available_sizes:
            size = SizeFormat.objects.get(id=i)
            available_sizes_list.append(size)

        shop_item.available_sizes.clear()
        shop_item.available_sizes.add(*available_sizes_list)

        return shop_item

    @classmethod
    def get_shop_item_by_link(cls, link):
        shop_item_id = [int(s) for s in re.findall(r'\b\d+\b', link)]
        return ShopItemService.get(id=shop_item_id[1])


# @classmethod
# def add_size_quantity(cls, stock_cart_id: int, size_format: SizeFormat, quantity: int):
#     try:
#         size_format = SizeFormat.objects.get(id=size_format.id)
#         stock_cart = StockCart.objects.get(id=stock_cart_id)
#     except StockCart.DoesNotExist:
#         raise ObjectNotFoundException(_('StockCart or SizeFormat not found'))
#     item_size_quantity, created = ShopItemSizeCount.objects.get_or_create(size_format=size_format,
#                                                                           stock_cart=stock_cart)
#     item_size_quantity.quantity = quantity
#     item_size_quantity.save()
#     return item_size_quantity
#
# @classmethod
# def get_or_create_stock_collection(cls, shop_item_id):
#     shop_item = ShopItemService.get(id=shop_item_id)
#     if not StockCollection.objects.filter(shop_item=shop_item).exists():
#         StockCollection.objects.create(shop_item=shop_item)
#
# @classmethod
# def fill_stock_collection_by_sizes(cls, shop_item_id, criteria_id, sizes):
#     shop_item = ShopItemService.get(id=shop_item_id)
#     criteria = CriteriaSubcategory.objects.get(id=criteria_id)
#     if StockCollection.objects.filter(shop_item=shop_item, criteria=None).exists():
#         stock_collection = StockCollection.objects.get(shop_item=shop_item, criteria=None)
#         stock_collection.criteria = criteria
#         stock_collection.save()
#     else:
#         stock_collection, _ = StockCollection.objects.get_or_create(shop_item=shop_item, criteria=criteria)
#     sizes_to_fill = []
#     for i in sizes:
#         sizes_to_fill.append(SizeFormat.objects.get(id=i))
#     stock_collection.available_sizes.clear()
#     stock_collection.available_sizes.add(*sizes_to_fill)
#     return stock_collection

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
def get_organization_delivery_info(cls, organization_id, start_time, end_time):
    return Transaction.objects.filter(
        Q(organization__id=organization_id) & Q(created_at__gte=start_time) & Q(created_at__lte=end_time))


@classmethod
def get_dict_data_for_deals(cls, queryset):
    employee_names = []
    employee_roles = []
    statuses = []
    types = []
    delivery_types = []
    delivery_orgs = []
    delivery_statuses = []
    delivery_display_dates = []
    delivery_display_times = []
    order_numbers = []
    transaction_dates = []
    transaction_times = []
    sum_before_discount = []
    currencies = []
    from_cashback = []
    discount_percent = []
    to_cashback = []
    savings = []
    final_amounts = []
    clients = []
    for i in queryset:
        employee_names.append(i.employee_name)
        employee_roles.append(i.employee_role)
        if i.status == 'accepted':
            statuses.append('Принят')
        elif i.status == 'rejected':
            statuses.append('Отклонен')
        elif i.status == 'in_progress':
            statuses.append('В ожидании')
        else:
            statuses.append(None)
        types.append(i.type)
        if i.delivery_type == 'self_pickup':
            delivery_types.append('Самовывоз')
        elif i.delivery_type == 'cash_courier':
            delivery_types.append('Наличными с курьером')
        else:
            delivery_types.append(i.delivery_type)

        try:
            org = Organization.objects.get(id=i.delivery_info.delivery_organization_id).title
            delivery_orgs.append(org)
        except Exception:
            delivery_orgs.append(None)
        try:
            if i.delivery_info.status == 'delivery_status_taken_for_delivery':
                delivery_statuses.append('Взято на доставку курьерской службой')
            elif i.delivery_info.status == 'delivery_status_set_for_delivery':
                delivery_statuses.append('Организация поставила заказа на доставку')
            elif i.delivery_info.status == 'delivery_status_rejected_by_delivery_service':
                delivery_statuses.append('Доставка отменена курьерской службой')
            elif i.delivery_info.status == 'delivery_status_accepted_by_delivery_service':
                delivery_statuses.append('Доставка подтверждена курьерской службой')
            elif i.delivery_info.status == 'delivery_status_delivered':
                delivery_statuses.append('Доставлено')
            else:
                delivery_statuses.append(None)
        except Exception:
            delivery_statuses.append(None)

        try:
            delivery_display_dates.append(i.display_time.date().strftime("%Y/%m/%d"))
        except Exception:
            delivery_display_dates.append(None)

        try:
            delivery_display_times.append(i.display_time.time().strftime("%H:%M:%S"))
        except Exception:
            delivery_display_times.append(None)
        order_numbers.append(i.id)
        transaction_dates.append(i.created_at.date().strftime("%Y/%m/%d"))
        transaction_times.append(i.created_at.time().strftime("%H:%M:%S"))
        sum_before_discount.append(str(i.original_amount))
        currencies.append(str(i.currency_id))
        from_cashback.append(str(i.from_cashback))
        discount_percent.append(i.discount_percent)
        to_cashback.append(str(i.to_cashback))
        savings.append(str(i.savings))
        final_amounts.append(i.final_amount)

        try:
            user = User.objects.get(id=i.client_id).full_name
            clients.append(user)
        except Exception:
            clients.append(None)

    dict_data = {_('Сотрудник'): employee_names,
                 _("Должность"): employee_roles,
                 _("Статус сделки"): statuses,
                 _("Вид сделки"): types,
                 _("Тип доставки"): delivery_types,
                 _("Курьерская служба"): delivery_orgs,
                 _("Статус доставки"): delivery_statuses,
                 _("Дата  доставки"): delivery_display_dates,
                 _("Время  доставки"): delivery_display_times,
                 _("Номер заказа"): order_numbers,
                 _("Дата"): transaction_dates,
                 _("Время"): transaction_times,
                 _("Сумма до скидки"): sum_before_discount,
                 _("Валюта"): currencies,
                 _("Снято с кэшбэка"): from_cashback,
                 _("Скидка%"): discount_percent,
                 _("Начисленно на кэшбэк"): to_cashback,
                 _("Экономия"): savings,
                 _("Сумма итого"): final_amounts,
                 _("Клиент"): clients,
                 }
    return dict_data


@classmethod
def get_dict_data_for_shop_item(cls, queryset):
    names = []
    subcategory = []
    price = []
    currency = []
    article = []
    number_transaction = []
    count = []
    for i in queryset:
        if i.fixed_cart:
            for j in i.fixed_cart.get('items'):
                shop_id = j['item']['id']
                try:
                    shop_item = ShopItem.objects.get(id=shop_id)
                    names.append(shop_item.name)
                    try:
                        subcategory.append(shop_item.subcategory.name)
                    except Exception:
                        subcategory.append(None)
                    price.append(j['item']['price'])
                    currency.append(i.currency_id)
                    article.append(shop_item.article)
                    number_transaction.append(i.id)
                    count.append(j['count'])
                except ShopItem.DoesNotExist:
                    names.append(None)
                    subcategory.append(None)
                    price.append(None)
                    currency.append(None)
                    article.append(None)
                    number_transaction.append(None)
                    count.append(None)
    dict_data = {_('Наименование товара'): names,
                 _('Категория товара'): subcategory,
                 _('Стоимость'): price,
                 _('Валюта'): currency,
                 _('Артикл'): article,
                 _('Номер заказа'): number_transaction,
                 _('Количество товара'): count,
                 }
    return dict_data
