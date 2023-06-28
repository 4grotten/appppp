from rest_framework import serializers

from common.models import File
from common.serializers import ImageSerializer, VideoSerializer
from shop.models import ItemLike, ItemCollection, ShopItem, ItemInstagramData
from shop.serializers.item_serializers import ItemInstagramImageSerializer, ItemInstagramVideoSerializer


class LikeSerializer(serializers.ModelSerializer):
    is_liked = serializers.BooleanField()

    class Meta:
        model = ItemLike
        fields = ('item', 'is_liked')


class BookmarkSerializer(serializers.ModelSerializer):
    is_bookmarked = serializers.BooleanField()

    class Meta:
        model = ItemLike
        fields = ('item', 'is_bookmarked')


class ItemBookmarkBulkDeleteSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.IntegerField(), required=True)


class ItemCollectionSerializer(serializers.ModelSerializer):
    in_collection = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    has_items = serializers.SerializerMethodField()

    class Meta:
        model = ItemCollection
        fields = ('id', 'name', 'in_collection', 'image', 'has_items')
        extra_kwargs = {
            'items': {'required': True}
        }

    def get_image(self, obj):
        if obj.image and obj.image in obj.items.all():
            serializer = ShopItemInCollectionSerializer(obj.image)
            return serializer.data
        first_item = obj.items.last()
        if first_item:
            serializer = ShopItemInCollectionSerializer(first_item)
            return serializer.data
        return None

    def get_has_items(self, obj):
        return obj.items.exists()

    def get_in_collection(self, obj):
        request = self.context.get('request')
        if request and request.method == 'GET':
            item_id = request.query_params.get('item')
            if item_id:
                item_exists = obj.items.filter(pk=item_id).exists()
                return item_exists
        return None


class ItemCollectionDetailUpdateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.IntegerField(), required=False)
    item_id = serializers.IntegerField(required=False)

    class Meta:
        model = ItemCollection
        fields = ('id', 'name', 'items', 'item_id')

class ItemCollectionCreateSerializer(serializers.ModelSerializer):
    items = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())

    class Meta:
        model = ItemCollection
        fields = ('name', 'items')
        extra_kwargs = {
            'items': {'required': True}
        }


class AddRemoveItemCollectionSerializer(serializers.Serializer):
    is_bookmarked = serializers.BooleanField()
    items = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())


class ShopItemInCollectionSerializer(serializers.ModelSerializer):
    instagram_data = serializers.SerializerMethodField()
    images = ImageSerializer(many=True)
    videos = VideoSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = ('id', 'images', 'videos', 'instagram_data')

    def get_instagram_data(self, item: ShopItem):
        videos = ItemInstagramData.objects.filter(item=item).exclude(video_url=None).order_by('created_at')
        images = ItemInstagramData.objects.filter(item=item, video_url=None).order_by('created_at')
        return dict(videos=ItemInstagramVideoSerializer(videos, many=True).data,
                    images=ItemInstagramImageSerializer(images, many=True).data)
