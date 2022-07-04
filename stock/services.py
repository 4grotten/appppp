from django.db.models import Q
from transliterate.utils import _

from imports.admin import User
from organizations.models import Organization
from shop.models import ShopItem
from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory
from transactions.models import Transaction


class StockService:

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
            statuses.append(i.status)
            types.append(i.type)
            delivery_types.append(i.delivery_type)
            try:
                org = Organization.objects.get(id=i.delivery_info.delivery_organization_id).title
                delivery_orgs.append(org)
            except Exception:
                delivery_orgs.append(None)

            try:
                delivery_statuses.append(i.delivery_info.status)
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
                        subcategory.append(shop_item.subcategory)
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
