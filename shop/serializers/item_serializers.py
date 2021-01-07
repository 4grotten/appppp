import datetime
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import ImageSerializer
from organizations.serializers.organization_serializers import ItemFeedOrganizationSerializer
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem, ItemInstagramData
from shop.serializers.category_serializers import ItemSubcategoryBriefSerializer
from shop.services.like_bookmark_services import LikeService, BookmarkService


class ItemSerializer(serializers.ModelSerializer):
    organization = ItemFeedOrganizationSerializer()
    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)
    instagram_data = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

    def get_instagram_data(self, item: ShopItem):
        videos = ItemInstagramData.objects.filter(item=item).exclude(video_url=None)
        images = ItemInstagramData.objects.filter(item=item, video_url=None)
        return dict(videos=ItemInstagramVideoSerializer(videos, many=True).data,
                    images=ItemInstagramImageSerializer(images, many=True).data)

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
            'instagram_data'
        )


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = (
            'id', 'organization', 'subcategory',
            'name', 'description',
            'price', 'discount', 'article',
            'instagram_link', 'images', 'youtube_links',
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

    def save(self, **kwargs):
        images = self.validated_data.get('images', [])
        for index, image in enumerate(images):
            image.order = index
            image.save(update_fields=('order',))

        instance = super().save(**kwargs)
        if instance.article == '' or instance.article is None:
            instance.article = f"ART{instance.id}"
            instance.save(update_fields=('article',))


class ItemChangePublishedSerializer(serializers.Serializer):
    is_published = serializers.BooleanField()
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())


class ItemInstagramDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemInstagramData
        fields = (
            'id', 'item', 'post_pk', 'thumbnail_url', 'video_url'
        )


class ItemInstagramVideoSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField()

    def get_thumbnail(self, obj):
        return obj.thumbnail_url

    class Meta:
        model = ItemInstagramData
        fields = (
            'thumbnail', 'video_url'
        )


class ItemInstagramImageSerializer(serializers.ModelSerializer):
    file = serializers.SerializerMethodField()
    large = serializers.SerializerMethodField()
    small = serializers.SerializerMethodField()
    medium = serializers.SerializerMethodField()

    def get_file(self, obj):
        return obj.thumbnail_url

    def get_large(self, obj):
        return obj.thumbnail_url

    def get_small(self, obj):
        return obj.thumbnail_url

    def get_medium(self, obj):
        return obj.thumbnail_url

    class Meta:
        model = ItemInstagramData
        fields = (
            'file', 'large', 'small', 'medium'
        )


class ItemListSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField()
    is_bookmarked = serializers.BooleanField()
    like_count = serializers.SerializerMethodField()
    instagram_data = serializers.SerializerMethodField()

    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)

    def get_instagram_data(self, item: ShopItem):
        videos = ItemInstagramData.objects.filter(item=item).exclude(video_url=None)
        images = ItemInstagramData.objects.filter(item=item, video_url=None)
        return dict(videos=ItemInstagramVideoSerializer(videos, many=True).data,
                    images=ItemInstagramImageSerializer(images, many=True).data)

    def get_like_count(self, item: ShopItem) -> int:
        return item.liked_users.count()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'description', 'article',
            'price', 'discount', 'instagram_link', 'is_published',
            'is_liked', 'is_bookmarked', 'like_count',
            'created_at', 'updated_at',
            'youtube_links', 'subcategory', 'images',
            'instagram_data'
        )


class ItemFeedSerializer(ItemListSerializer):
    organization = ItemFeedOrganizationSerializer()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'description', 'article',
            'price', 'discount', 'instagram_link', 'is_published',
            'is_liked', 'is_bookmarked', 'like_count',
            'created_at', 'updated_at',
            'youtube_links', 'subcategory', 'images', 'organization',
            'instagram_data'
        )


class StartDateTimeSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(required=False, default=datetime.datetime.utcnow().isoformat())


class ItemInCartSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, item: ShopItem) -> dict:
        image = item.images.filter(order=0).first()
        return ImageSerializer(image, context=self.context).data

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'price', 'discounted_price', 'image'
        )
