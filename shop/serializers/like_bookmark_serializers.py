from rest_framework import serializers

from common.models import File
from common.serializers import ImageSerializer
from shop.models import ItemLike, ItemCollection, ShopItem


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

    class Meta:
        model = ItemCollection
        fields = ('id', 'name', 'in_collection', 'image')
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

    class Meta:
        model = ItemCollection
        fields = ('id', 'name', 'image', 'items')

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
