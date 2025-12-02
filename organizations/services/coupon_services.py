from decimal import ROUND_HALF_UP, Decimal

from django.db.models import Exists, OuterRef

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
        ).order_by("-created_at")
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
        coupons = data.pop("coupons")
        initial_amount: Decimal = data.get("initial_amount")
        final_amount = initial_amount
        discount_sum = Decimal("0.00")

        coupons = (
            cls.__model.objects.filter(pk__in=coupons).order_by("coupon_type").all()
        )

        for coupon in coupons:
            discount = (final_amount * Decimal(coupon.percent)) / Decimal("100")
            discount_sum += discount
            final_amount -= discount

        final_amount = final_amount.quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

        result = {"discount_sum": discount_sum, "final_amount": final_amount}
        return result

    @classmethod
    def get_list(cls, org_id: int, user):
        qs = (
            cls.__model.objects.filter(organization_id=org_id)
            .annotate(used=Exists(CouponUsage.objects.filter(coupon=OuterRef("pk"))))
            .prefetch_related("coupon_usage")
            .order_by("used")
        )

        return qs
