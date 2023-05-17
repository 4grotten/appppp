import re

from django.db.models import Q, Min, Max

from imports.admin import User
from organizations.models import Organization
from stock.models import ShopItemSetStock, ShopItemLinksSetStock, ShopItemSizeCount
from transactions.models import Transaction
from transliterate.utils import _

from common.exceptions import ObjectNotFoundException
from shop.models import ShopItem, RentalPeriod
from shop.services.item_services import ShopItemService
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory


class StockService:

    @classmethod
    def get_size_format(cls, **filters):
        try:
            return SizeFormat.objects.get(**filters)
        except SizeFormat.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

    @classmethod
    def get_list_size_formats(cls, **filters):
        try:
            return SizeFormat.objects.filter(**filters)
        except SizeFormat.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

    @classmethod
    def add_shop_items_sets(cls, main_item: int, shop_items=None):
        try:
            main_item = ShopItem.objects.get(id=main_item)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))

        shop_item_stock, created = ShopItemSetStock.objects.get_or_create(main_shop_item=main_item)
        shop_items_list = []
        for i in shop_items:
            shop_item = ShopItemService.get(id=i)
            if not ShopItemLinksSetStock.objects.filter(main_shop_item=main_item, shop_item=shop_item):
                shop_items_list.append(shop_item)
        shop_item_stock.shop_item.clear()
        shop_item_stock.shop_item.add(*shop_items_list)

    @classmethod
    def add_shop_link_items_sets(cls, main_item: int, shop_item_links=None):
        try:
            main_item = ShopItem.objects.get(id=main_item)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))

        ShopItemLinksSetStock.objects.filter(main_shop_item=main_item).delete()

        for link in shop_item_links:
            shop_item_by_link = [int(s) for s in re.findall(r'\b\d+\b', link)]
            shop_item = ShopItemService.get(id=shop_item_by_link[0])
            if not ShopItemSetStock.objects.filter(main_shop_item=main_item, shop_item=shop_item):
                ShopItemLinksSetStock.objects.get_or_create(main_shop_item=main_item, shop_item=shop_item, link=link)

    @classmethod
    def add_shop_items_size_count(cls, main_item, size=None, count=None):
        shop_item = ShopItemService.get(id=main_item)
        shop_item_size_count, _ = ShopItemSizeCount.objects.get_or_create(main_shop_item=shop_item, size=size)
        shop_item_size_count.count = count
        shop_item_size_count.save()
        return shop_item_size_count

    @classmethod
    def get_not_choosen_size(cls, main_item):
        try:
            main_shop_item = ShopItemService.get(id=main_item)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))
        size_count = ShopItemSizeCount.objects.filter(main_shop_item=main_shop_item)
        array = []
        for i in size_count:
            array.append(i.size)
        array_result = []
        for i in main_shop_item.available_sizes.all():
            if i not in array:
                array_result.append(i)
        array_result = sorted(array_result, key=lambda k: k.order)
        return array_result

    @classmethod
    def add_available_sizes(cls, shop_item_id: int, available_sizes=None):
        try:
            shop_item = ShopItem.objects.get(id=shop_item_id)
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('Shop item not found'))

        format_criteria_list = []

        for format in shop_item.available_sizes.all():
            format_criteria_list.append(format.format_criteria)

        available_sizes_list = []

        for i in available_sizes:
            size = SizeFormat.objects.get(id=i)
            available_sizes_list.append(size)
            if size.format_criteria not in format_criteria_list:
                shop_item.available_sizes.clear()
                ShopItemSizeCount.objects.filter(main_shop_item=shop_item).delete()

        current_available_sizes = ShopItemSizeCount.objects.filter(main_shop_item=shop_item)
        for size in current_available_sizes:
            if size.size not in available_sizes_list:
                size.delete()

        shop_item.available_sizes.clear()
        shop_item.available_sizes.add(*available_sizes_list)

        return shop_item

    @classmethod
    def get_shop_item_by_link(cls, link):
        shop_item_id = [int(s) for s in re.findall(r'\b\d+\b', link)]
        return ShopItemService.get(id=shop_item_id[0])

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
        if start_time and end_time:
            return Transaction.objects.filter(
                Q(organization__id=organization_id) & Q(created_at__gte=start_time) & Q(created_at__lte=end_time))\
                .order_by('-id')
        else:
            return Transaction.objects.filter(organization__id=organization_id).order_by('-id')

    @classmethod
    def get_rental_info(cls, item, start_time, end_time):
        if start_time and end_time:
            return Transaction.objects.filter(
                Q(booking__item=item) & Q(created_at__gte=start_time) & Q(created_at__lte=end_time)) \
                .order_by('-id')
        else:
            return Transaction.objects.filter(booking__item=item).order_by('-id')

    @classmethod
    def get_organization_products_info(cls, organization_id, start_time, end_time):
        if start_time and end_time:
            return Transaction.objects.filter(
                Q(organization__id=organization_id) & Q(created_at__gte=start_time) & Q(created_at__lte=end_time) & Q(
                    booking__item__purchase_type='product')
            ).order_by('-id')
        else:
            return Transaction.objects.filter(
                Q(organization__id=organization_id) & Q(booking__item__purchase_type='product')
            ).order_by('-id')

    @classmethod
    def get_organization_rental_info(cls, organization_id, start_time, end_time):
        if start_time and end_time:
            return Transaction.objects.filter(
                Q(organization__id=organization_id) & Q(created_at__gte=start_time) & Q(created_at__lte=end_time) & Q(
                    booking__item__purchase_type='rent')
            ).order_by('-id')
        else:
            return Transaction.objects.filter(
                Q(organization__id=organization_id) & Q(booking__item__purchase_type='rent')
            ).order_by('-id')

    @classmethod
    def get_organization_delivery_min_and_max_date_info(cls, organization_id):
        date_dictionary = Transaction.objects.filter(organization__id=organization_id).aggregate(Min('created_at'), Max('created_at'))
        start_date = date_dictionary['created_at__min'].strftime("%Y-%m-%d")
        end_date = date_dictionary['created_at__max'].strftime("%Y-%m-%d")
        return start_date, end_date

    @classmethod
    def get_rental_min_and_max_date_info(cls, item):
        date_dictionary = Transaction.objects.filter(booking__item=item).aggregate(Min('created_at'),
                                                                                                 Max('created_at'))
        start_date = date_dictionary['created_at__min'].strftime("%Y-%m-%d")
        end_date = date_dictionary['created_at__max'].strftime("%Y-%m-%d")
        return start_date, end_date

    @classmethod
    def get_stock_set_items(cls, main_shop_item):
        try:
            return ShopItem.objects.filter(
                Q(shop_items_set_stocks__main_shop_item=main_shop_item) |
                Q(shop_items_link_set_stocks__main_shop_item=main_shop_item)
            )
        except ShopItem.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

    @classmethod
    def get_list_of_set_stock_by_shop_item(cls, **filters):
        try:
            shop_item_stock = ShopItemSetStock.objects.get(**filters)
        except ShopItemSetStock.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItemSetStock not found'))
        return shop_item_stock.shop_item.all()

    @classmethod
    def get_link_set_stock_by_shop_item(cls, **filters):
        try:
            return ShopItemLinksSetStock.objects.filter(**filters)
        except ShopItemLinksSetStock.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItemLinksSetStock not found'))

    @classmethod
    def delete_stock_by_shop_item_id(cls, shop_item):
        ShopItemSizeCount.objects.filter(main_shop_item=shop_item).delete()
        ShopItemSetStock.objects.filter(main_shop_item=shop_item).delete()
        ShopItemLinksSetStock.objects.filter(main_shop_item=shop_item).delete()
        shop_item.available_sizes.clear()


    @classmethod
    def get_dict_data_for_deals(cls, queryset):
        employee_names = []
        employee_roles = []
        statuses = []
        types = []
        delivery_types = []
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
        phone_number = []
        for i in queryset:
            try:
                booking = i.booking
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
                delivery_types.append("Аренда")
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
                    phone = User.objects.get(id=i.client_id).phone_number
                    clients.append(user)
                    phone_number.append(phone)
                except Exception:
                    clients.append(None)
                    phone_number.append(None)
            except Transaction.booking.RelatedObjectDoesNotExist:
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
                    phone = User.objects.get(id=i.client_id).phone_number
                    clients.append(user)
                    phone_number.append(phone)
                except Exception:
                    clients.append(None)
                    phone_number.append(None)
                continue

        dict_data = {_('Сотрудник'): employee_names,
                     _("Должность"): employee_roles,
                     _("Статус сделки"): statuses,
                     _("Вид сделки"): types,
                     _("Тип доставки"): delivery_types,
                     _("Номер заказа"): order_numbers,
                     _("Дата"): transaction_dates,
                     _("Время"): transaction_times,
                     _("Сумма до скидки"): sum_before_discount,
                     _("Валюта"): currencies,
                     _("Снято с кэшбэка"): from_cashback,
                     _("Скидка%"): discount_percent,
                     _("Начислено на кэшбэк"): to_cashback,
                     _("Экономия"): savings,
                     _("Сумма итого"): final_amounts,
                     _("Клиент"): clients,
                     _("Номер телефона"): phone_number,
                     }
        return dict_data

    @classmethod
    def get_dict_data_for_rental_deals(cls, queryset):
        employee_names = []
        employee_roles = []
        statuses = []
        types = []
        delivery_types = []
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
        phone_number = []
        for i in queryset:
            try:
                booking = i.booking
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
                delivery_types.append("Аренда")
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
                    phone = User.objects.get(id=i.client_id).phone_number
                    clients.append(user)
                    phone_number.append(phone)
                except Exception:
                    clients.append(None)
                    phone_number.append(None)
            except Transaction.booking.RelatedObjectDoesNotExist:
                continue

        dict_data = {_('Сотрудник'): employee_names,
                     _("Должность"): employee_roles,
                     _("Статус сделки"): statuses,
                     _("Вид сделки"): types,
                     _("Тип доставки"): delivery_types,
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
                     _("Номер телефона"): phone_number,
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
        size = []
        delivery_orgs = []
        delivery_statuses = []
        delivery_display_dates = []
        delivery_display_times = []
        for i in queryset:
            if i.fixed_cart:
                items = i.fixed_cart.get('items')
                if items:
                    for j in items:
                        shop_id = j['item']['id']
                        try:
                            shop_item = ShopItem.objects.get(id=shop_id, purchase_type='product')
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
                            item_size = j.get('size', None)
                            item_size = item_size['size'] if item_size else None
                            size.append(item_size)

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


                        except ShopItem.DoesNotExist:
                            names.append(None)
                            subcategory.append(None)
                            price.append(None)
                            currency.append(None)
                            article.append(None)
                            number_transaction.append(None)
                            count.append(None)
                            size.append(None)
                            delivery_orgs.append(None)
                            delivery_statuses.append(None)
                            delivery_display_dates.append(None)
                            delivery_display_times.append(None)
        dict_data = {_('Наименование товара'): names,
                     _('Категория товара'): subcategory,
                     _('Стоимость'): price,
                     _('Валюта'): currency,
                     _('Артикул'): article,
                     _('Номер заказа'): number_transaction,
                     _('Количество товара'): count,
                     _('Размер товара'): size,
                     _("Курьерская служба"): delivery_orgs,
                     _("Статус доставки"): delivery_statuses,
                     _("Дата  доставки"): delivery_display_dates,
                     _("Время  доставки"): delivery_display_times,
                     }
        return dict_data

    @classmethod
    def get_dict_data_for_rentals(cls, queryset):
        names = []
        subcategory = []
        price = []
        currency = []
        article = []
        number_transaction = []
        rent_time_type = []
        start_date = []
        start_time = []
        end_date = []
        end_time = []
        clients = []

        for i in queryset:
            try:
                booking = i.booking
                item = booking.item
                try:
                    shop_item = ShopItem.objects.get(id=item.id, purchase_type='rent')
                    names.append(shop_item.name)
                    try:
                        subcategory.append(shop_item.subcategory.name)
                    except Exception:
                        subcategory.append(None)
                    price.append(shop_item.price)
                    currency.append(i.currency_id)
                    article.append(shop_item.article)
                    number_transaction.append(i.id)
                    rent_time_type.append(shop_item.rental_period.rent_time_type)
                    start_date.append(booking.start_time.strftime("%Y/%m/%d"))
                    start_time.append(booking.start_time.strftime("%H:%M"))
                    end_date.append(booking.end_time.strftime("%Y/%m/%d"))
                    end_time.append(booking.end_time.strftime("%H:%M"))

                    try:
                        user = User.objects.get(id=i.client_id).full_name
                        clients.append(user)
                    except Exception:
                        clients.append(None)
                except ShopItem.DoesNotExist:
                    names.append(None)
                    subcategory.append(None)
                    price.append(None)
                    currency.append(None)
                    article.append(None)
                    number_transaction.append(None)
                    rent_time_type.append(None)
                    start_time.append(None)
                    end_time.append(None)
                    clients.append(None)
            except Transaction.booking.RelatedObjectDoesNotExist:
                continue
        dict_data = {_('Наименование товара'): names,
                     _('Категория товара'): subcategory,
                     _('Стоимость'): price,
                     _('Валюта'): currency,
                     _('Артикл'): article,
                     _('Номер заказа'): number_transaction,
                     _('Тип времени аренды'): rent_time_type,
                     _('Дата начала'): start_date,
                     _('Время начала'): start_time,
                     _('Дата окончания'): end_date,
                     _('Время окончания'): end_time,
                     _('Клиент'): clients,
                     }
        return dict_data
