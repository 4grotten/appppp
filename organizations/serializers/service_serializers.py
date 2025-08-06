from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Organization
from organizations.models import Service
from organizations.serializers.categories_serializers import OrganizationTypeSerializer
from shop.models import ShopItem


class ServiceSerializer(serializers.ModelSerializer):
    icon = ImageSerializer()
    banner = ImageSerializer()

    class Meta:
        model = Service
        fields = (
            "id",
            "is_discounts",
            "is_entertainment",
            "is_map",
            "is_resume",
            "is_wholesale",
            "is_application",
            "ordering",
            "name",
            "icon",
            "banner",
            "description",
        )


class OrganizationServiceSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    time_working = serializers.SerializerMethodField(read_only=True)

    def get_time_working(self, organization: Organization):
        working_type = organization.time_working
        if working_type == 1:
            return "around_the_clock"
        if working_type == 2:
            return "open"
        if working_type == 3:
            return "closed"

    class Meta:
        model = Organization
        fields = (
            "id",
            "title",
            "image",
            "types",
            "opens_at",
            "closes_at",
            "time_working",
            "verification_status",
            "avg_check",
            "currency",
            "full_location",
        )


class ItemServiceSerializer(serializers.ModelSerializer):
    images = ImageSerializer()
    organization_name = serializers.CharField(
        source="organization.title", read_only=True
    )
    types = OrganizationTypeSerializer(
        many=True, source="organization.types", read_only=True
    )
    organization_id = serializers.IntegerField(source="organization.id", read_only=True)
    category = serializers.CharField(source="subcategory.title", read_only=True)
    old_price = serializers.SerializerMethodField()
    instagram = serializers.URLField(source="instagram_link", read_only=True)

    class Meta:
        model = ShopItem
        fields = (
            "id",
            "name",
            "images",
            "price",
            "old_price",
            "discount_price",
            "currency",
            "category",
            "description",
            "organization_name",
            "types",
            "organization_id",
            "instagram",
        )

    def get_old_price(self, obj):
        if obj.discount and obj.discount > 0:
            return obj.price
        return None
