from django.core.exceptions import ObjectDoesNotExist
from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from common.exceptions import ObjectNotFoundException
from organizations.models import Organization
from organizations.services.organization_promo_services import OrganizationPromoService
from organizations.services.organization_services import OrganizationService
from search_indexes.documents.items import ShopItemDocument
from shop.models import ItemCategory


class ImageIndexSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    file = serializers.CharField(read_only=True)
    large = serializers.CharField(read_only=True)
    medium = serializers.CharField(read_only=True)
    small = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class PhoneIndexSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    phone_number = serializers.CharField(read_only=True)


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


class ItemsOrganizationIndexSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    currency = serializers.SerializerMethodField()
    image = ImageIndexSerializer()
    title = serializers.CharField()
    phone_numbers = PhoneIndexSerializer(many=True)
    promo_cashback = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    types = TypesIndexOrganizationSerializer(many=True)

    def get_permissions(self, organization):
        if self.context['request'].user.is_anonymous:
            return None
        try:
            organization = Organization.objects.get(pk=organization.id)
        except ObjectDoesNotExist:
            raise ObjectNotFoundException
        return OrganizationService.get_user_permissions_dict(organization=organization,
                                                             user=self.context['request'].user)

    def get_promo_cashback(self, organization):
        return OrganizationPromoService.get_available_promo_cashback_amount(organization=organization)

    def get_currency(self, org):
        return org.currency.code


class ItemCategorySerializer(serializers.Serializer):
    class Meta:
        model = ItemCategory
        fields = ('id', 'name', 'icon')


class SubcategoryIndexSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()

    def get_icon(self, subcategory):
        if subcategory:
            return subcategory['category']['icon'].to_dict()

    def get_name(self, subcategory):
        current_lang = self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE')
        if subcategory:
            if current_lang:
                for key in subcategory:
                    if key.endswith('_' + current_lang[0:2]):
                        return subcategory[key]
            return subcategory['name_en']


class ShopItemsDocumentSerializer(DocumentSerializer):
    organization = ItemsOrganizationIndexSerializer()
    is_bookmarked = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    subcategory = SubcategoryIndexSerializer()

    def get_like_count(self, item):
        if item.liked_users:
            return len(item.liked_users)
        return 0

    def get_is_liked(self, item):
        user = self.context.get('request').user
        if user.id and item.liked_users:
            return user.id in item.liked_users
        return False

    def get_is_bookmarked(self, item):
        user = self.context.get('request').user
        if user.id and item.bookmarked_users:
            return user.id in item.bookmarked_users
        return False

    class Meta:
        document = ShopItemDocument
        fields = (
            'article', 'created_at', 'description', 'description_lang', 'discount', 'id', 'images', 'instagram_data',
            'instagram_link', 'is_bookmarked', 'is_hidden', 'is_liked', 'is_published', 'is_updated', 'like_count',
            'name', 'name_lang', 'organization', 'price', 'removed_at', 'subcategory', 'updated_at', 'youtube_links',
        )

# from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
#
# from search_indexes.documents.items import ShopItemDocument


# class ShopItemsDocumentSerializer(DocumentSerializer):
#     """Serializer for address document."""
#
#     class Meta(object):
#         """Meta options."""
#
#         document = ShopItemDocument
#         fields = (
#             'id',
#             'article',
#             'name',
#             'description',
#             'price',
#             'is_published',
#             'is_updated',
#             'removed_at',
#             'youtube_links',
#             'name_lang',
#             'created_at',
#             'updated_at',
#             'description_lang',
#             'discount',
#             'instagram_link',
#             'is_hidden',
#             'instagram_data',
#             'bookmarked_users',
#             'liked_users',
#             'subcategory',
#             'images',
#             'organization',
#         )
