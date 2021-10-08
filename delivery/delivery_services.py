from datetime import timedelta

from django.contrib.gis.geos import Point
from django.db.models import Q, Count, Case, When
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequestException
from delivery.models import DeliveryInfo, DeliveryActionHistory
from organizations.models import Organization
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

            created = DeliveryInfo.objects.create(*args, location=point, country=country, city=city, **kwargs)

            return created
        except Exception as e:
            raise BadRequestException(_(f'Could not add delivery info , {e}'))

    @classmethod
    def _get_queryset(self, user: User):
        delivery_service_organizations = list(user.owned_organizations.filter(is_delivery_service=True))
        memberships = list(user.memberships.filter(
            Q(organization__is_delivery_service=True,
              organization__is_active=True,
              organization__is_banned=False,
              organization__is_deleted=False,
              ) &
            Q(
                Q(role__can_see_stats=True) |
                Q(role__can_edit_organization=True) |
                Q(role__can_deliver=True)
            )
        ).distinct())

        delivery_service_organizations.extend([membership.organization for membership in memberships])
        countries = [o.country for o in delivery_service_organizations]
        queryset = Cart.objects.filter(
            Q(
                transaction__delivery_info__country__in=countries,
                transaction__status=Transaction.ACCEPTED,
                transaction__delivery_info__status__in=(
                    DeliveryInfo.DELIVERY_STATUS_SET_FOR_DELIVERY,
                    DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE,))
            | Q(
                transaction__delivery_info__delivery_organization__in=delivery_service_organizations,
                transaction__delivery_info__country__in=countries,
                transaction__status=Transaction.ACCEPTED,
                transaction__delivery_info__status__in=(
                    DeliveryInfo.DELIVERY_STATUS_TAKEN_FOR_DELIVERY,
                ),
            )
        ).exclude(
            transaction__delivery_info__history__delivery_organization__in=delivery_service_organizations,
            transaction__delivery_info__history__status=DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE,

        ).annotate(
            relevancy=Count(
                Case(When(transaction__delivery_info__status=DeliveryInfo.DELIVERY_STATUS_TAKEN_FOR_DELIVERY, then=1)))
        ).order_by('-relevancy', '-transaction__delivery_info__updated_at')
        return queryset

    @classmethod
    def get_set_for_delivery_count(cls, user: User) -> int:
        queryset = DeliveryInfoService._get_queryset(user).filter(
            transaction__delivery_info__status=DeliveryInfo.DELIVERY_STATUS_SET_FOR_DELIVERY)
        return queryset.distinct().count()

    @classmethod
    def get_all_items_count(cls, user: User) -> int:
        queryset = DeliveryInfoService._get_queryset(user)
        return queryset.distinct().count()

    @classmethod
    def get_available_orders(cls, user: User) -> list:
        queryset = DeliveryInfoService._get_queryset(user)
        return queryset.distinct()

    @classmethod
    def get_history_items(cls, user: User) -> list:
        delivery_service_organizations = list(user.owned_organizations.filter(
            is_delivery_service=True,
            is_active=True,
            is_banned=False,
            is_deleted=False
        ))
        
        memberships = list(user.memberships.filter(
            Q(organization__is_delivery_service=True,
              organization__is_active=True,
              organization__is_banned=False,
              organization__is_deleted=False,
              ) &
            Q(
                Q(role__can_see_stats=True) |
                Q(role__can_edit_organization=True) |
                Q(role__can_deliver=True)
            )
        ).distinct())

        delivery_service_organizations.extend([membership.organization for membership in memberships])

        countries = [o.country for o in delivery_service_organizations]
        return Cart.objects.filter(
            Q(
                transaction__delivery_info__country__in=countries,
                transaction__status=Transaction.ACCEPTED,
                transaction__delivery_info__delivery_organization__in=delivery_service_organizations,
                transaction__delivery_info__status__in=(
                    DeliveryInfo.DELIVERY_STATUS_DELIVERED,
                ),

            ) | Q(
                transaction__delivery_info__delivery_organization__in=delivery_service_organizations,
                transaction__status=Transaction.ACCEPTED,
                transaction__delivery_info__history__delivery_organization__in=delivery_service_organizations,
                transaction__delivery_info__history__status=DeliveryInfo.DELIVERY_STATUS_REJECTED_BY_DELIVERY_SERVICE
            )
        ).order_by('-id').distinct('id')

    @classmethod
    def add_action_history_item(cls, delivery_info: DeliveryInfo, delivery_organization: Organization, status: str):
        DeliveryActionHistory.objects.create(delivery_info=delivery_info, delivery_organization=delivery_organization,
                                             status=status)
