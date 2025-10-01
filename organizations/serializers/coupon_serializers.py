from rest_framework import serializers

from organizations.models import Coupon, DiscountCard
from shop.models import ShopItem


class DiscountCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCard
        fields = ["type", "percent"]


class ProductCouponSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = ShopItem
        fields = ["id", "name", "description", "price", "images"]

    def get_images(self, obj):
        return [img.file.url for img in obj.images.all()]


class CouponListSerializer(serializers.ModelSerializer):
    discount = DiscountCouponSerializer()
    product = ProductCouponSerializer()

    class Meta:
        model = Coupon
        fields = [
            "id",
            "discount",
            "product",
            "percent",
            "description",
            "expire_date",
            "image",
        ]


class ValidateCreateCouponSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = Coupon
        fields = (
            "product",
            "discount",
            "percent",
            "description",
            "image",
            "expire_date",
            "always_active",
            "is_active",
            "is_updating",
            "coupon_type",
        )

    def validate(self, attrs):
        coupon_type = attrs.get("coupon_type")
        always_active = attrs.get("always_active")
        expire_date = attrs.get("expire_date")

        if coupon_type == "discount":
            if not attrs.get("discount"):
                raise serializers.ValidationError(
                    {
                        "discount": "discount field is required if coupon type is discount"
                    }
                )
            if attrs.get("product"):
                raise serializers.ValidationError(
                    {"product": "Не указывайте product для купона типа discount"}
                )
        elif coupon_type == "product":
            if not attrs.get("product"):
                raise serializers.ValidationError(
                    {"product": "product field is required if coupon type is product"}
                )
            if attrs.get("discount"):
                raise serializers.ValidationError(
                    {"discount": "Не указывайте discount для купона типа product"}
                )

        if always_active and expire_date:
            raise serializers.ValidationError(
                {"expire date": "please remove expire_date if its always active"}
            )

        return attrs


class CouponDetailSerializer(serializers.ModelSerializer):
    discount = DiscountCouponSerializer()
    product = ProductCouponSerializer()

    class Meta:
        model = Coupon
        fields = [
            "id",
            "discount",
            "product",
            "percent",
            "description",
            "expire_date",
            "is_updating",
            "is_active",
            "always_active",
            "image",
        ]
