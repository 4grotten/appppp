from decimal import Decimal

from django.db.models import Exists, OuterRef, Prefetch

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
            cls.__model.objects.filter(organization_id=organization_id, is_active=True)
            .select_related("product")
            .prefetch_related("product__images")
        ).order_by("-updated_at", "-created_at")
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
                organization_id=org_id,
                is_active=True,
            )
            .exclude(Exists(used))
            .select_related("product")
            .prefetch_related("product__organization", "product__images")
        )

        return coupons

    @classmethod
    def calculate(cls, data: dict):
        coupons_list = data["coupons"]
        coupons_qs = (
            cls.__model.objects.filter(id__in=coupons_list)
            .select_related("product")
            .all()
        )
        discount_sum = 0
        discount_percent = 0

        for coupon in coupons_qs:
            if coupon.coupon_type == cls.__model.PRODUCT:
                if (
                    coupon.product
                    and coupon.product.price
                    and coupon.percent is not None
                ):
                    discount_sum += coupon.product.price * Decimal(coupon.percent / 100)
            if coupon.coupon_type == cls.__model.DISCOUNT:
                if coupon.percent is not None:
                    discount_percent = coupon.percent

        return {"discount_sum": discount_sum, "discount_perc": discount_percent}

    @classmethod
    def get_list(cls, org_id: int, user):
        qs = (
            cls.__model.objects.filter(organization_id=org_id)
            .annotate(
                used=Exists(
                    CouponUsage.objects.filter(coupon=OuterRef("pk"), user=user)
                )
            )
            .prefetch_related(
                Prefetch(
                    "coupon_usage",
                    queryset=CouponUsage.objects.filter(user=user),
                    to_attr="user_coupon_usage",
                )
            )
            .order_by("used", "-updated_at", "-created_at")
        )
        print(qs.query)

        return qs
