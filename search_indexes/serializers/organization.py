from rest_framework import serializers

from organizations.services.card_services import DiscountCardService
from organizations.services.organization_promo_services import OrganizationPromoService
from search_indexes.documents.organizations import OrganizationDocument


class ImageIndexSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    file = serializers.CharField(read_only=True)
    large = serializers.CharField(read_only=True)
    medium = serializers.CharField(read_only=True)
    small = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class TypesIndexOrganizationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.SerializerMethodField()

    def get_title(self, types):
        current_lang = self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE')
        if types:
            if current_lang:
                for key in types:
                    if key.endswith('_' + current_lang[0:2]):
                        return types[key]
            return types['title_en']


class OrganizationIndexSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField()
    promo_cashback = serializers.SerializerMethodField()
    discounts = serializers.SerializerMethodField()
    types = TypesIndexOrganizationSerializer(many=True)
    image = ImageIndexSerializer()
    verification_status = serializers.CharField(read_only=True)
    avg_check = serializers.DecimalField(decimal_places=2, max_digits=16)

    def get_promo_cashback(self, organization):
        return OrganizationPromoService.get_available_promo_cashback_amount(organization=organization.id)

    def get_discounts(self, organization):
        return DiscountCardService.get_unique_discount_percents_to_display(organization=organization.id)

    class Meta:
        document = OrganizationDocument
        fields = (
            'id', 'title', 'promo_cashback', 'discounts', 'types', 'image', 'types', 'verification_status', 'country',
            'city', 'avg_check'
        )

# from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
#
# from search_indexes.documents.organizations import OrganizationDocument
#
#
# class OrganizationIndexSerializer(DocumentSerializer):
#     """Serializer for address document."""
#
#     class Meta(object):
#         """Meta options."""
#
#         document = OrganizationDocument
#         fields = (
#             'id', 'title', 'promo_cashback', 'types', 'images', 'types', 'verification_status', 'country',
#             'city'
#         )
