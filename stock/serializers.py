from rest_framework import serializers

from stock.models import FormatSize, ShopItemSize


class FormatSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatSize
        fields = ('id', 'name',)


class ShopItemSizeSerializer(serializers.ModelSerializer):
    format_size = FormatSizeSerializer()

    class Meta:
        model = ShopItemSize
        fields = ('id', 'size', 'format_size',)
