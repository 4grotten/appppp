from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import ImageSerializer
from organizations.serializers.organization_serializers import OrganizationWithTypeImageSerializer
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem, Complaint
from shop.serializers.category_serializers import ItemSubcategoryBriefSerializer
from shop.services.like_bookmark_services import LikeService, BookmarkService


class ItemSerializer(serializers.ModelSerializer):
    organization = OrganizationWithTypeImageSerializer()
    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)

    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

    def get_is_liked(self, item: ShopItem) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return LikeService.is_item_liked_by_user(item=item, user=user)

    def get_is_bookmarked(self, item: ShopItem) -> bool:
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return BookmarkService.is_item_bookmarked_by_user(item=item, user=user)

    def get_like_count(self, item: ShopItem) -> int:
        return item.liked_users.count()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'description', 'article',
            'price', 'discount',
            'instagram_link', 'is_published', 'is_liked', 'is_bookmarked', 'like_count',
            'created_at', 'updated_at',
            'youtube_links', 'subcategory', 'images', 'organization',
        )


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = (
            'id', 'organization', 'subcategory',
            'name', 'description',
            'price', 'discount', 'article',
            'instagram_link', 'images', 'youtube_links'
        )

    def validate(self, attrs):
        user = self.context['request'].user
        organization = attrs['organization']

        subcategory = attrs.get('subcategory', None)
        subcategory_organization = getattr(subcategory, 'organization', None)
        if subcategory_organization is not None and not subcategory_organization == organization:
            raise NotAcceptableException('Organization does not have this subcategory')

        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException('No rights to edit organization')

        return attrs


class ItemChangePublishedSerializer(serializers.Serializer):
    is_published = serializers.BooleanField()
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())


class ItemFeedSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField()
    is_bookmarked = serializers.BooleanField()
    like_count = serializers.SerializerMethodField()

    organization = OrganizationWithTypeImageSerializer()
    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)

    def get_like_count(self, item: ShopItem) -> int:
        return item.liked_users.count()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'description', 'article',
            'price', 'discount', 'is_published',
            'is_liked', 'is_bookmarked', 'like_count',
            'created_at', 'updated_at',
            'youtube_links', 'subcategory', 'images', 'organization',
        )


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ('item', 'reason',)

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return attrs
