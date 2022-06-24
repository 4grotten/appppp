from rest_framework import serializers

from stock.models import FormatCriteria, SizeFormat, CriteriaSubcategory, StockCart, ShopItemSizeCount


class CriteriaSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CriteriaSubcategory
        fields = ('id', 'name',)


class FormatCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormatCriteria
        fields = ('id', 'name',)


class SizeFormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeFormat
        fields = ('id', 'size',)


class CreateStokeCartSerializer(serializers.Serializer):
    available_size = serializers.ListSerializer(child=serializers.IntegerField(), required=False, default=[])


class StockCartSerializer(serializers.ModelSerializer):
    available_size = SizeFormatSerializer(many=True)

    class Meta:
        model = StockCart
        fields = ('id', 'shop_item', 'available_size')


class AddSizeQuantitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItemSizeCount
        fields = ('id', 'size_format', 'quantity')

