from decimal import Decimal
from typing import Optional

from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.constants import HOMEPAGE_ORGS_IN_CATEGORIES_COUNT
from organizations.models import OrganizationType, OrganizationCategory, Organization
from organizations.services.card_services import DiscountCardService
from organizations.services.organization_promo_services import OrganizationPromoService
from organizations.services.organization_services import (
    OrganizationService,
    OrganizationJSONService,
)


class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = (
            "id",
            "title",
        )


class OrganizationJSONTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    # title = serializers.CharField(required=False, allow_null=True)

    def to_representation(self, instance):

        if isinstance(instance, int):
            print(instance)
            try:
                org_type = OrganizationType.objects.only("id", "title").get(id=instance)
                return {"id": org_type.id, "title": org_type.title}
            except OrganizationType.DoesNotExist:
                return {"id": instance, "title": None}
        return super().to_representation(instance)


class OrganizationCategorySerializer(serializers.ModelSerializer):
    types = OrganizationTypeSerializer(many=True)

    class Meta:
        model = OrganizationCategory
        fields = ("id", "name", "types")


class OrganizationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationCategory
        fields = ("id", "name")


class HomepageOrganizationsSerializer(serializers.ModelSerializer):
    organizations = serializers.SerializerMethodField()
    organizations_count = serializers.SerializerMethodField()

    def get_organizations(self, category: OrganizationCategory):
        partner = self.context["partner"]
        country = self.context["country"]
        city = self.context["city"]
        # organizations = OrganizationService.get_random_organizations_in_category(
        #     category=category, partner=partner, country=country, city=city
        # )[:HOMEPAGE_ORGS_IN_CATEGORIES_COUNT]
        organizations = OrganizationJSONService.get_organizations_in_category(
            partner=partner, country=country, city=city, category=category
        )

        organizations = organizations[:HOMEPAGE_ORGS_IN_CATEGORIES_COUNT]
        return OrganizationWithDiscountsJSONSerializer(
            organizations,
            many=True,
            context={"request": self.context.get("request", None)},
        ).data
        # return OrganizationWithDiscountsSerializer(
        #     organizations,
        #     many=True,
        #     context={"request": self.context.get("request", None)},
        # ).data

    def get_organizations_count(self, category: OrganizationCategory):
        # using annotated value from OrganizationCategoryService.get_nonempty_categories
        return category.orgs_count

    class Meta:
        model = OrganizationCategory
        fields = ("id", "name", "organizations_count", "organizations")


class OrganizationWithDiscountsSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    discounts = serializers.SerializerMethodField()
    promo_cashback = serializers.SerializerMethodField()

    def get_promo_cashback(self, organization) -> Optional[Decimal]:
        return OrganizationPromoService.get_available_promo_cashback_amount(
            organization=organization
        )

    def get_discounts(self, organization: int) -> list:
        return DiscountCardService.get_unique_discount_percents_to_display(
            organization=organization
        )

    class Meta:
        model = Organization
        fields = (
            "id",
            "title",
            "promo_cashback",
            "discounts",
            "types",
            "image",
            "verification_status",
            "is_private",
            "is_banned",
            "verification_status",
            "subscription_status",
        )


class OrganizationWithDiscountsJSONSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    promo_cashback = serializers.SerializerMethodField()
    discounts = serializers.SerializerMethodField()
    types = serializers.ListField(child=serializers.IntegerField())
    image = serializers.DictField()
    verification_status = serializers.CharField()
    is_private = serializers.BooleanField()
    is_banned = serializers.BooleanField()
    subscription_status = serializers.CharField(allow_null=True, required=False)

    def get_promo_cashback(self, organization: dict) -> Optional[Decimal]:
        return OrganizationPromoService.get_available_promo_cashback_amount_json(
            organization=organization
        )

    def get_discounts(self, organization: dict) -> list:
        return DiscountCardService.get_unique_discount_percents_to_display(
            organization=organization["id"]
        )
