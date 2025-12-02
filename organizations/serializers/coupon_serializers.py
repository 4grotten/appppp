from rest_framework import serializers

from organizations.models import Coupon
from shop.models import ShopItem


class ProductCouponSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()

    class Meta:
        model = ShopItem
        fields = ["id", "name", "description", "price", "images"]

    def get_images(self, obj):
        return [img.file.url for img in obj.images.all()]


class CouponListSerializer(serializers.ModelSerializer):
    product = ProductCouponSerializer(required=False)

    class Meta:
        model = Coupon
        fields = [
            "id",
            "product",
            "percent",
            "description",
            "expire_date",
            "is_updating",
            "image",
            "coupon_type",
        ]


class ValidateCreateCouponSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = Coupon
        fields = (
            "product",
            "percent",
            "description",
            "image",
            "expire_date",
            "always_active",
            "is_active",
            "is_updating",
            "coupon_type",
            "organization",
        )

    def validate(self, attrs):
        coupon_type = attrs.get("coupon_type")
        always_active = attrs.get("always_active")
        expire_date = attrs.get("expire_date")
        if coupon_type == "product":
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
    product = ProductCouponSerializer()

    class Meta:
        model = Coupon
        fields = [
            "id",
            "product",
            "percent",
            "description",
            "expire_date",
            "is_updating",
            "is_active",
            "always_active",
            "coupon_type",
            "image",
        ]

    def update(self, instance, validated_data):
        product_data = validated_data.pop("product", None)

        if product_data:
            instance.product_id = product_data.get("id")

        return super().update(instance, validated_data)


class CalculateCouponValidateSerializer(serializers.Serializer):
    coupons = serializers.ListField(child=serializers.IntegerField(), write_only=True)


class CouponListForUserSerializer(serializers.ModelSerializer):
    product = ProductCouponSerializer()
    used_on = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            "id",
            "product",
            "percent",
            "description",
            "expire_date",
            "is_updating",
            "is_active",
            "always_active",
            "coupon_type",
            "used",
            "used_on",
            "image",
        ]

    def get_used_on(self, obj):
        if obj.used:
            coupon_usage = obj.coupon_usage.first()
            return coupon_usage.created_at
        else:
            return None
