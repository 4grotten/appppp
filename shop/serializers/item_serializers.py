import datetime

from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.models import File, FileVideo
from common.serializers import ImageSerializer, VideoSerializer
from organizations.models import HotlinkCollectionItem, Organization, BlockedUser
from organizations.serializers.organization_serializers import ItemFeedOrganizationSerializer
from organizations.services.organization_services import OrganizationService
from shop.models import ShopItem, ItemInstagramData, RentalPeriod
from shop.serializers.category_serializers import ItemSubcategoryBriefSerializer
from shop.services.cart_services import CartItemService
from shop.services.like_bookmark_services import LikeService, BookmarkService
from stock.models import ShopItemSizeCount
from stock.serializers import SizeFormatByItemSerializer, ShopItemSizeCountSerializer


class ItemSetRetrieveSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    currency = serializers.CharField(source='organization.currency')
    has_in_stock = serializers.SerializerMethodField()

    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_image(self, item: ShopItem):
        image = item.images.first()
        thumbnail = item.videos.first()
        if image:
            image = File.objects.get(id=image.id)
            return ImageSerializer(image, context=self.context).data
        else:
            thumbnail = FileVideo.objects.get(id=thumbnail.id)
            return VideoSerializer(thumbnail, context=self.context).data

    class Meta:
        model = ShopItem
        fields = ('id', 'price', 'discount', 'currency', 'image', 'has_in_stock')


class ItemRetrieveSerializer(serializers.ModelSerializer):
    organization = ItemFeedOrganizationSerializer()
    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)
    videos = VideoSerializer(many=True)
    instagram_data = serializers.SerializerMethodField()

    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    can_comment = serializers.SerializerMethodField(default=True, read_only=True)
    available_sizes = serializers.SerializerMethodField()
    set_items = serializers.SerializerMethodField()
    has_in_stock = serializers.SerializerMethodField()

    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_set_items(self, item: ShopItem):
        items = ShopItem.objects.filter(
            Q(shop_items_set_stocks__main_shop_item=item) |
            Q(shop_items_link_set_stocks__main_shop_item=item)
        )[:2]
        return ItemSetRetrieveSerializer(items, many=True, context=self.context).data

    def get_available_sizes(self, item: ShopItem):
        sizes = item.available_sizes.all().order_by('order')
        if sizes.exists() and ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            item_size_counts = ShopItemSizeCount.objects.filter(main_shop_item=item).values_list('size_id', flat=True)
            sizes = item.available_sizes.filter(id__in=item_size_counts).order_by('order')
        elif sizes.first() is None and ShopItemSizeCount.objects.filter(main_shop_item=item, size=None).exists():
            sizes = ShopItemSizeCount.objects.filter(main_shop_item=item, size=None)
            return ShopItemSizeCountSerializer(sizes, many=True, context={'shop_item': item, 'request': self.context['request']}).data
        return SizeFormatByItemSerializer(sizes, many=True,
                                          context={'shop_item': item, 'request': self.context['request']}).data

    def get_instagram_data(self, item: ShopItem):
        videos = ItemInstagramData.objects.filter(item=item).exclude(video_url=None)
        images = ItemInstagramData.objects.filter(item=item, video_url=None).order_by('pk')
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

    def get_comment_count(self, item: ShopItem) -> int:
        return item.comments.count()

    def get_can_comment(self, item: ShopItem) -> bool:
        if self.context['request'].user:
            user = self.context['request'].user
            blocked_users = BlockedUser.objects.filter(organization_id=item.organization.id, user=user.id).values_list('user_id', flat=True).distinct()
            return not BlockedUser.objects.filter(user_id__in=blocked_users).exists()


    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount',
            'instagram_link', 'is_published', 'is_hidden', 'is_liked', 'is_bookmarked', 'like_count', 'comment_count',
            'can_comment', 'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images', 'videos', 'organization',
            'instagram_data', 'is_updated', 'available_sizes', 'set_items', 'has_in_stock'
        )


class ItemCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = (
            'id', 'organization', 'subcategory',
            'name', 'name_lang', 'description', 'description_lang',
            'price', 'discount', 'article',
            'instagram_link', 'images', 'videos', 'youtube_links',
            'is_updated', 'removed_at'
        )
        read_only_fields = ['name_lang', 'description_lang']

    def validate(self, attrs):
        user = self.context['request'].user
        organization = attrs['organization']

        subcategory = attrs.get('subcategory', None)
        subcategory_organization = getattr(subcategory, 'organization', None)
        if subcategory_organization is not None and not subcategory_organization == organization:
            raise NotAcceptableException(_('Organization does not have this subcategory'))

        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException(_('No rights to edit organization'))

        return attrs

    def update(self, instance, validated_data):
        validated_data.pop('organization', None)
        if 'price' in validated_data and validated_data.get('price') is None:
            CartItemService.delete_item_from_all_carts(self.instance)

        return super().update(instance, validated_data)

    def save(self, **kwargs):
        images = self.validated_data.get('images', [])
        for index, image in enumerate(images):
            image.order = index
            image.save(update_fields=('order',))

        videos = self.validated_data.get('videos', [])
        for index, video in enumerate(videos):
            video.order = index
            video.save(update_fields=('order',))

        instance = super().save(**kwargs)
        if instance.article == '' or instance.article is None:
            instance.article = f"ART{instance.id}"
            instance.save(update_fields=('article',))

        if self.validated_data.get('price') == 0.00:
            instance.price = None
            instance.save()

        organization_data = self.validated_data.get('organization')
        Organization.objects.filter(id=organization_data.id).update(add_item_date=datetime.datetime.now())


class RentalPeriodSerializer(serializers.ModelSerializer):

    class Meta:
        model = RentalPeriod
        fields = (
            'id', 'start_date', 'end_date', 'start_time', 'end_time'
        )


class ItemRentalCreateUpdateSerializer(serializers.ModelSerializer):
    # longitude = serializers.FloatField(allow_null=True, required=False)
    # latitude = serializers.FloatField(allow_null=True, required=False)
    rental_period = RentalPeriodSerializer(required=False)

    class Meta:
        model = ShopItem
        fields = (
            'id', 'organization', 'subcategory',
            'name', 'name_lang', 'description', 'description_lang',
            'price', 'discount', 'article',
            'instagram_link', 'images', 'videos', 'youtube_links',
            'is_updated', 'removed_at', 'purchase_type', 'address', 'rental_period', 'full_location'
        )
        read_only_fields = ['name_lang', 'description_lang']

    def validate(self, attrs):
        user = self.context['request'].user
        organization = attrs['organization']

        subcategory = attrs.get('subcategory', None)
        subcategory_organization = getattr(subcategory, 'organization', None)
        if subcategory_organization is not None and not subcategory_organization == organization:
            raise NotAcceptableException(_('Organization does not have this subcategory'))

        if not OrganizationService.user_can_edit_organization(user=user, organization=attrs['organization']):
            raise NotAcceptableException(_('No rights to edit organization'))

        return attrs

    def update(self, instance, validated_data):
        validated_data.pop('organization', None)
        if 'price' in validated_data and validated_data.get('price') is None:
            CartItemService.delete_item_from_all_carts(self.instance)

        return super().update(instance, validated_data)

    def save(self, **kwargs):
        images = self.validated_data.get('images', [])
        for index, image in enumerate(images):
            image.order = index
            image.save(update_fields=('order',))

        videos = self.validated_data.get('videos', [])
        for index, video in enumerate(videos):
            video.order = index
            video.save(update_fields=('order',))

        instance = super().save(**kwargs)

        instance.purchase_type = 'rent'
        instance.save(update_fields=('purchase_type',))
        if instance.article == '' or instance.article is None:
            instance.article = f"ART{instance.id}"
            instance.save(update_fields=('article',))

        if self.validated_data.get('price') == 0.00:
            instance.price = None
            instance.save()

        organization_data = self.validated_data.get('organization')
        Organization.objects.filter(id=organization_data.id).update(add_item_date=datetime.datetime.now())


class RentItemsPeriodSerializer(serializers.ModelSerializer):

    class Meta:
        model = RentalPeriod
        fields = (
            'id', 'rent_time_type', 'start_date', 'end_date', 'start_time', 'end_time'
        )


class ItemChangePublishedSerializer(serializers.Serializer):
    is_published = serializers.BooleanField()
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())


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


class ItemsSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang',
            'price', 'is_published', 'updated_at', 'images'
        )


class ItemListSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField()
    is_bookmarked = serializers.BooleanField()
    like_count = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    instagram_data = serializers.SerializerMethodField()

    subcategory = ItemSubcategoryBriefSerializer()
    images = ImageSerializer(many=True)

    def get_instagram_data(self, item: ShopItem):
        videos = ItemInstagramData.objects.filter(item=item).exclude(video_url=None).order_by('created_at')
        images = ItemInstagramData.objects.filter(item=item, video_url=None).order_by('created_at')
        return dict(videos=ItemInstagramVideoSerializer(videos, many=True).data,
                    images=ItemInstagramImageSerializer(images, many=True).data)

    def get_like_count(self, item: ShopItem) -> int:
        return item.liked_users.count()

    def get_comment_count(self, item: ShopItem) -> int:
        return item.comments.count()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount', 'instagram_link', 'is_published',
            'is_liked', 'is_bookmarked', 'like_count', 'comment_count',
            'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images',
            'instagram_data', 'is_updated'
        )
        read_only_fields = ['name_lang', 'description_lang']


class SubscriptionItemSerializer(ItemListSerializer):
    organization = ItemFeedOrganizationSerializer()
    videos = VideoSerializer(many=True)
    available_sizes = serializers.SerializerMethodField()
    set_items = serializers.SerializerMethodField()
    has_in_stock = serializers.SerializerMethodField()

    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_set_items(self, item: ShopItem):
        items = ShopItem.objects.filter(
            Q(shop_items_set_stocks__main_shop_item=item) |
            Q(shop_items_link_set_stocks__main_shop_item=item)
        )[:2]
        return ItemSetRetrieveSerializer(items, many=True, context=self.context).data

    def get_available_sizes(self, item: ShopItem):
        sizes = item.available_sizes.all().order_by('order')
        if sizes.exists() and ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            item_size_counts = ShopItemSizeCount.objects.filter(main_shop_item=item).values_list('size_id', flat=True)
            sizes = item.available_sizes.filter(id__in=item_size_counts).order_by('order')
        elif sizes.first() is None and ShopItemSizeCount.objects.filter(main_shop_item=item, size=None).exists():
            sizes = ShopItemSizeCount.objects.filter(main_shop_item=item, size=None)
            return ShopItemSizeCountSerializer(sizes, many=True,
                                               context={'shop_item': item, 'request': self.context['request']}).data
        return SizeFormatByItemSerializer(sizes, many=True,
                                          context={'shop_item': item, 'request': self.context['request']}).data

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount', 'instagram_link', 'is_published',
            'is_liked', 'is_bookmarked', 'like_count', 'comment_count',
            'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images', 'videos', 'organization',
            'instagram_data', 'is_updated', 'available_sizes', 'set_items', 'has_in_stock'
        )
        read_only_fields = ['name_lang', 'description_lang']


class ItemFeedSerializer(ItemListSerializer):
    organization = ItemFeedOrganizationSerializer()
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S%z')
    videos = VideoSerializer(many=True)
    subcategory = ItemSubcategoryBriefSerializer()
    available_sizes = serializers.SerializerMethodField()
    set_items = serializers.SerializerMethodField()
    has_in_stock = serializers.SerializerMethodField()
    can_comment = serializers.SerializerMethodField(default=True, read_only=True)

    def get_has_in_stock(self, item: ShopItem):
        if ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            return ShopItemSizeCount.objects.filter(main_shop_item=item).aggregate(total=Sum('count'))['total'] > 0
        else:
            return True

    def get_set_items(self, item: ShopItem):
        items = ShopItem.objects.filter(
            Q(shop_items_set_stocks__main_shop_item=item) |
            Q(shop_items_link_set_stocks__main_shop_item=item)
        )[:2]
        return ItemSetRetrieveSerializer(items, many=True, context=self.context).data

    def get_available_sizes(self, item: ShopItem):
        sizes = item.available_sizes.all().order_by('order')
        if sizes.exists() and ShopItemSizeCount.objects.filter(main_shop_item=item).exists():
            item_size_counts = ShopItemSizeCount.objects.filter(main_shop_item=item).values_list('size_id', flat=True)
            sizes = item.available_sizes.filter(id__in=item_size_counts).order_by('order')
        elif sizes.first() is None and ShopItemSizeCount.objects.filter(main_shop_item=item, size=None).exists():
            sizes = ShopItemSizeCount.objects.filter(main_shop_item=item, size=None)
            return ShopItemSizeCountSerializer(sizes, many=True,
                                               context={'shop_item': item, 'request': self.context['request']}).data
        return SizeFormatByItemSerializer(sizes, many=True,
                                          context={'shop_item': item, 'request': self.context['request']}).data

    def get_can_comment(self, item: ShopItem) -> bool:
        if self.context['request'].user:
            user = self.context['request'].user
            blocked_users = BlockedUser.objects.filter(organization_id=item.organization.id, user=user.id).values_list('user_id', flat=True).distinct()
            return not BlockedUser.objects.filter(user_id__in=blocked_users).exists()

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'name_lang', 'description', 'description_lang', 'article',
            'price', 'discount', 'instagram_link', 'is_published', 'is_hidden',
            'is_liked', 'is_bookmarked', 'like_count',
            'created_at', 'updated_at', 'removed_at',
            'youtube_links', 'subcategory', 'images', 'videos', 'organization',
            'instagram_data', 'is_updated', 'comment_count', 'can_comment', 'available_sizes', 'set_items', 'has_in_stock'
        )
        read_only_fields = ['name_lang', 'description_lang']


class StartDateTimeSerializer(serializers.Serializer):
    start_time = serializers.DateTimeField(required=False, default=None)


class ItemInCartSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    def get_image(self, item: ShopItem) -> dict:
        image = item.images.filter(order=0).first()
        video = item.videos.filter(order=0).first()
        if image:
            return ImageSerializer(image, context=self.context).data
        if video:
            return ImageSerializer(video.thumbnail, context=self.context).data
        image_data = None
        insta_data = ItemInstagramData.objects.filter(item=item, thumbnail_url__isnull=False).first()
        if insta_data is not None:
            item_video_thumbnail_url = insta_data.thumbnail_url
            image_data = {
                "id": 0,
                "file": item_video_thumbnail_url,
                "name": "Cart thumbnail",
                "large": item_video_thumbnail_url,
                "medium": item_video_thumbnail_url,
                "small": item_video_thumbnail_url
            }
        return image_data

    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'price', 'discounted_price', 'image'
        )


class ItemInHotlinkSerializer(ItemInCartSerializer):
    class Meta:
        model = ShopItem
        fields = (
            'id', 'name', 'image'
        )


class ItemInHotlinkCollectionSerializer(ItemInCartSerializer):
    subcategory_name = serializers.CharField(source='subcategory.name', default=None)
    currency = serializers.CharField(source='organization.currency.code')
    is_selected = serializers.SerializerMethodField()

    class Meta:
        model = ShopItem
        fields = ('id', 'name', 'subcategory_name', 'price', 'discounted_price', 'currency', 'is_selected', 'image')

    def get_is_selected(self, item: ShopItem) -> bool:
        if 'hotlink' not in self.context:
            return False
        return HotlinkCollectionItem.objects.filter(hotlink=self.context['hotlink'], item=item).exists()
