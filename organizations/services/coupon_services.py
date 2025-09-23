from organizations.models import Coupon
from common.exceptions import CouponException


class CouponServiceClass:
    __model = Coupon

    @classmethod
    def get(cls, *args, **kwargs):
        organization_id = kwargs.pop("organization_id", None)[0]
        if not organization_id:
            raise CouponException
        queryset = (
            cls.__model.objects.filter(
                product__organization__id=organization_id, is_active=True
            )
            .select_related("product", "discount")
            .prefetch_related("product__organization", "product__images")
        )
        return queryset

    @classmethod
    def create_coupon(cls, *args, **kwargs):
        coupon = cls.__model.objects.create(**kwargs)

        return coupon
