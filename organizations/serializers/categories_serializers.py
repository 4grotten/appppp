from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.constants import HOMEPAGE_ORGS_IN_CATEGORIES_COUNT
from organizations.models import OrganizationType, OrganizationCategory, Organization
from organizations.services.card_services import DiscountCardService
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


class HomepageOrganizationsSerializer(serializers.ModelSerializer):
    organizations = serializers.SerializerMethodField()
    organizations_count = serializers.SerializerMethodField()

    def get_organizations(self, category: OrganizationCategory):
        partner = self.context.get('partner', None)
        organizations = OrganizationService.get_organizations_in_category(category=category, partner=partner,
                                                                          )[:HOMEPAGE_ORGS_IN_CATEGORIES_COUNT]
        return OrganizationWithDiscountsSerializer(organizations, many=True).data

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

    def get_discounts(self, organization: Organization) -> list:
        return DiscountCardService.get_unique_discount_percents_to_display(organization=organization)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'types', 'image', 'discounts')


class OrganizationAndCategorySerializer(serializers.Serializer):
    category = serializers.PrimaryKeyRelatedField(queryset=OrganizationCategory.objects.all())
    partner = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True),
                                                 default=None)


class PartnerQueryParamSerializer(serializers.Serializer):
    partner = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True), default=None)
