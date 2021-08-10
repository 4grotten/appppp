from django.contrib.gis.geos import Point
from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException
from delivery.models import DeliveryInfo
from shop.models import Cart
from transactions.models import Transaction
from users.models import User


class DeliveryInfoService:
    @classmethod
    def create(cls, longitude, latitude, *args, **kwargs):
        try:
            if longitude and latitude:
                point = Point(longitude, latitude)
            else:
                point = None
            transaction = kwargs['transaction']
            transaction.delivery_type = 'cash_courier'
            transaction.save()
            country = transaction.cart.organization.country
            city = transaction.cart.organization.city
            return DeliveryInfo.objects.create(*args, location=point, country=country, city=city, **kwargs)
        except Exception as e:
            raise BadRequestException(_(f'Could not add delivery info , {e}'))

    @classmethod
    def get_all_items_count(cls, user: User) -> int:
        delivery_service_organizations = list(user.owned_organizations.filter(is_delivery_service=True))
        countries = [o.country for o in delivery_service_organizations]
        return DeliveryInfo.objects.filter(
            country__in=countries,
            status__in=(
                DeliveryInfo.DELIVERY_STATUS_SET_FOR_DELIVERY,
                DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE
            )).count()

    @classmethod
    def get_available_orders(cls, user: User) -> list:
        delivery_service_organizations = list(user.owned_organizations.filter(is_delivery_service=True))
        countries = [o.country for o in delivery_service_organizations]
        queryset = Cart.objects.filter(
            transaction__delivery_info__country__in=countries,
            transaction__status=Transaction.ACCEPTED,
            transaction__delivery_info__status__in=(
                DeliveryInfo.DELIVERY_STATUS_SET_FOR_DELIVERY,
                DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE,
            )).order_by('-created_at')
        in_progress = Cart.objects.filter(
            transaction__delivery_info__country__in=countries,
            transaction__status=Transaction.ACCEPTED,
            transaction__delivery_info__status__in=(
                DeliveryInfo.DELIVERY_STATUS_TAKEN_FOR_DELIVERY,
            ),
            transaction__delivery_info__delivery_organization__in=delivery_service_organizations
        ).order_by('-created_at')
        return list(in_progress) + list(queryset)

    @classmethod
    def get_history_items(cls, user: User) -> list:
        delivery_service_organizations = list(user.owned_organizations.filter(is_delivery_service=True))
        countries = [o.country for o in delivery_service_organizations]
        return list(Cart.objects.filter(
            transaction__delivery_info__country__in=countries,
            transaction__status=Transaction.ACCEPTED,
            transaction__delivery_info__status__in=(
                DeliveryInfo.DELIVERY_STATUS_DELIVERED,
            )).order_by('-created_at'))
