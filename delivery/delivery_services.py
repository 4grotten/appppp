from django.contrib.gis.geos import Point

from common.exceptions import BadRequestException
from delivery.models import DeliveryInfo
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
            return DeliveryInfo.objects.create(*args, location=point, **kwargs)
        except Exception as e:
            raise BadRequestException(f'Could not add delivery info , {e}')

    @classmethod
    def get_all_items_count(cls, user: User) -> int:
        delivery_service_organizations = list(user.owned_organizations.filter(is_delivery_service=True))
        countries = [o.country for o in delivery_service_organizations]
        return DeliveryInfo.objects.filter(country__in=countries).count()

