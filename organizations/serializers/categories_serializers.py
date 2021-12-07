from decimal import Decimal
from typing import Optional

from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.constants import HOMEPAGE_ORGS_IN_CATEGORIES_COUNT
from organizations.models import OrganizationType, OrganizationCategory, Organization
from organizations.services.card_services import DiscountCardService
from organizations.services.organization_promo_services import OrganizationPromoService
from organizations.services.organization_services import OrganizationService


class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = ('id', 'title',)


class OrganizationCategorySerializer(serializers.ModelSerializer):
    types = OrganizationTypeSerializer(many=True)

    class Meta:
        model = OrganizationCategory
        fields = ('id', 'name', 'types')


class OrganizationDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationCategory
        fields = ('id', 'name')


class HomepageOrganizationsSerializer(serializers.ModelSerializer):
    organizations = serializers.SerializerMethodField()
    organizations_count = serializers.SerializerMethodField()

    def get_organizations(self, category: OrganizationCategory):
        partner = self.context['partner']
        country = self.context['country']
        city = self.context['city']
        organizations = OrganizationService.get_random_organizations_in_category(
            category=category, partner=partner, country=country, city=city)[:HOMEPAGE_ORGS_IN_CATEGORIES_COUNT]
        return OrganizationWithDiscountsSerializer(organizations, many=True,
                                                   context={'request': self.context.get('request', None)}).data

    def get_organizations_count(self, category: OrganizationCategory):
        # using annotated value from OrganizationCategoryService.get_nonempty_categories
        return category.orgs_count

    class Meta:
        model = OrganizationCategory
        fields = ('id', 'name', 'organizations_count', 'organizations')


class OrganizationWithDiscountsSerializer(serializers.ModelSerializer):
    image = ImageSerializer()
    types = OrganizationTypeSerializer(many=True)
    discounts = serializers.SerializerMethodField()
    promo_cashback = serializers.SerializerMethodField()

    def get_promo_cashback(self, organization: Organization) -> Optional[Decimal]:
        return OrganizationPromoService.get_available_promo_cashback_amount(organization=organization)

    def get_discounts(self, organization: Organization) -> list:
        return DiscountCardService.get_unique_discount_percents_to_display(organization=organization)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'promo_cashback', 'discounts', 'types', 'image', 'verification_status' )
