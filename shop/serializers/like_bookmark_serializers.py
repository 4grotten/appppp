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
    video = serializers.SerializerMethodField()
    has_items = serializers.SerializerMethodField()

    class Meta:
        model = ItemCollection
        fields = ('id', 'name', 'in_collection', 'image', 'video', 'has_items')
        extra_kwargs = {
            'items': {'required': True}
        }

    def get_image(self, obj):
        if obj.image:
            serializer = ImageSerializer(obj.image)
            return serializer.data
        first_item = obj.items.last()
        if first_item:
            images = first_item.images.first()
            if images:
                serializer = ImageSerializer(images)
                return serializer.data
        return None

    def get_video(self, obj):
        if obj.video:
            serializer = VideoSerializer(obj.video)
            return serializer.data
        first_item = obj.items.last()
        if first_item:
            videos = first_item.videos.first()
            if videos:
                serializer = VideoSerializer(videos)
                return serializer.data
        return None

    def get_has_items(self, obj):
        return obj.items.exists()

    # def get_instagram_data(self, obj):
    #     first_item = obj.items.last()
    #     print(first_item)
    #     if first_item:
    #         videos = ItemInstagramData.objects.filter(item=first_item).exclude(video_url=None)
    #         images = ItemInstagramData.objects.filter(item=first_item, video_url=None).order_by('pk')
    #         return dict(videos=ItemInstagramVideoSerializer(videos, many=True).data,
    #                     images=ItemInstagramImageSerializer(images, many=True).data)

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
