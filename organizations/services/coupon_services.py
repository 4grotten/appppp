from django.db.models import Exists, OuterRef, Q

from common.exceptions import CouponException
from organizations.models import Coupon, CouponUsage


class CouponServiceClass:
    __model = Coupon

    @classmethod
    def get(cls, *args, **kwargs):
        organization_id = kwargs.pop("organization_id", None)
        if not organization_id:
            raise CouponException
        queryset = (
            cls.__model.objects.filter(
                product__organization_id=organization_id, is_active=True
            )
            .select_related("product")
            .prefetch_related("product__organization", "product__images")
        )
        return queryset

    @classmethod
    def create_coupon(cls, *args, **kwargs):
        coupon = cls.__model.objects.create(**kwargs)

        return coupon

    @classmethod
    def get_detail(cls, id):
        coupon = cls.__model.objects.filter(pk=id).select_related("product").first()
        return coupon

    @classmethod
    def get_available(cls, org_id, user):
        used = CouponUsage.objects.filter(user=user, coupon_id=OuterRef("id"))
        coupons = (
            cls.__model.objects.filter(
                Q(product__organization_id=org_id)
                | Q(discount__organization_id=org_id),
                is_active=True,
            )
            .exclude(Exists(used))
            .select_related("product")
            .prefetch_related("product__organization", "product__images")
        )

        return coupons
