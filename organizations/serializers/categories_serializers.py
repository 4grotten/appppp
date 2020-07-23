from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import OrganizationType, OrganizationCategory, Organization
from organizations.services.card_services import DiscountCardService


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

    def get_organizations(self, category: OrganizationCategory):
        # ToDo: limit number of returning organizations
        organizations = Organization.objects.filter(is_active=True, types__in=category.types.all()).distinct()
        return OrganizationWithDiscountsSerializer(organizations, many=True).data

    class Meta:
        model = OrganizationCategory
        fields = ('id', 'name', 'organizations',)


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
