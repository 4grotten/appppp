from decimal import Decimal

from django.db.models import Exists, OuterRef, Prefetch
from django.db.models import Case, When, F, BooleanField, OuterRef, Exists
from django.utils import timezone

from common.exceptions import CouponException
from organizations.models import Coupon, CouponUsage
from transactions.models import Transaction


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
    def get_available(cls, org_id, transaction_id):
        transaction = Transaction.objects.get(id=transaction_id)
        user = transaction.client
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        qs = (
            cls.__model.objects.filter(organization_id=org_id)
            .annotate(
                used_ever=Exists(
                    CouponUsage.objects.filter(
                        coupon=OuterRef("pk"), 
                        user=user
                    )
                ),
                used_today=Exists(
                    CouponUsage.objects.filter(
                        coupon=OuterRef("pk"), 
                        user=user,
                        created_at__gte=today_start 
                    )
                )
            )
            .annotate(
                used=Case(
                    When(always_active=True, then=F('used_today')),
                    default=F('used_ever'),
                    output_field=BooleanField()
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

        return qs


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

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        qs = (
            cls.__model.objects.filter(organization_id=org_id)
            .annotate(
                used_ever=Exists(
                    CouponUsage.objects.filter(
                        coupon=OuterRef("pk"), 
                        user=user
                    )
                ),
                used_today=Exists(
                    CouponUsage.objects.filter(
                        coupon=OuterRef("pk"), 
                        user=user,
                        created_at__gte=today_start
                    )
                )
            )
            .annotate(
                used=Case(
                    When(always_active=True, then=F('used_today')),
                    default=F('used_ever'),
                    output_field=BooleanField()
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
        # print(qs.query)

        return qs
