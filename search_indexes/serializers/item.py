from django_elasticsearch_dsl_drf.serializers import DocumentSerializer
from rest_framework import serializers

from common.models import File
from organizations.serializers.organization_serializers import OrgPhoneNumberSerializer
from search_indexes.documents.items import ShopItemDocument


class ImageIndexOrganizationSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    file = serializers.CharField(read_only=True)
    large = serializers.CharField(read_only=True)
    medium = serializers.CharField(read_only=True)
    small = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)


class OrganizationRenameFieldSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    currency = serializers.SerializerMethodField()
    image = ImageIndexOrganizationSerializer()
    title = serializers.CharField()
    phone_numbers = serializers.CharField()

    def get_currency(self, org):
        return org.currency.code

    class Meta:
        fields = (
            'currency', 'id', 'title', 'image', 'phone_numbers'
        )


class ShopItemsDocumentSerializer(DocumentSerializer):
    organization = OrganizationRenameFieldSerializer()
    is_bookmarked = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

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
            'id', 'article', 'created_at', 'updated_at', 'name', 'name_lang', 'description', 'description_lang',
            'discount', 'instagram_data', 'instagram_link', 'is_hidden', 'images',
            'subcategory', 'is_published', 'is_updated', 'like_count', 'price', 'removed_at', 'youtube_links',
            'organization'
        )
