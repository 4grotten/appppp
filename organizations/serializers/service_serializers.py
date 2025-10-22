from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Organization
from organizations.models import Service
from organizations.serializers.categories_serializers import (
    OrganizationTypeSerializer,
    OrganizationJSONTypeSerializer,
)
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


class ImageJSONSerializer(serializers.Serializer):
    # name = serializers.URLField(read_only=True)
    file = serializers.ImageField(read_only=True)
    large = serializers.ImageField(read_only=True)
    medium = serializers.ImageField(read_only=True)
    small = serializers.ImageField(read_only=True)
    # is_watermarked = serializers.BooleanField(write_only=True)

    # class Meta:
    #     model = File
    #     fields = (
    #         "id",
    #         "file",
    #         "name",
    #         "large",
    #         "medium",
    #         "small",
    #         # "is_watermarked",
    #     )
    #     read_only_fields = ("name",)

    # def get_name(self, obj):
    #     return obj.file.name.split("/")[-1]


class OrganizationJSONServiceSerializer(serializers.Serializer):
    image = ImageJSONSerializer()
    types = OrganizationJSONTypeSerializer(many=True)
    time_working = serializers.SerializerMethodField(read_only=True)
    id = serializers.IntegerField()
    title = serializers.CharField()
    opens_at = serializers.TimeField()
    closes_at = serializers.TimeField()
    verification_status = serializers.CharField()
    avg_check = serializers.IntegerField()
    currency = serializers.CharField()
    full_location = serializers.DictField()

    def get_time_working(self, organization: dict):
        working_type = organization.get("time_working")
        if working_type == 1:
            return "around_the_clock"
        if working_type == 2:
            return "open"
        if working_type == 3:
            return "closed"

    # class Meta:
    #     model = Organization
    #     fields = (
    #         "id",
    #         "title",
    #         "image",
    #         "types",
    #         "opens_at",
    #         "closes_at",
    #         "time_working",
    #         "verification_status",
    #         "avg_check",
    #         "currency",
    #         "full_location",
    #     )


class ItemServiceSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    organization_name = serializers.CharField(
        source="organization.title", read_only=True
    )
    types = OrganizationTypeSerializer(
        many=True, source="organization.types", read_only=True
    )
    organization_id = serializers.IntegerField(source="organization.id", read_only=True)
    category = serializers.CharField(source="subcategory.title", read_only=True)
    instagram = serializers.URLField(source="instagram_link", read_only=True)

    class Meta:
        model = ShopItem
        fields = (
            "id",
            "name",
            "images",
            "price",
            "currency",
            "category",
            "discount",
            "description",
            "organization_name",
            "types",
            "organization_id",
            "instagram",
        )
