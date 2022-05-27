from rest_framework import serializers

from common.serializers import SmallImageSerializer
from shop.models import Complaint, ShopItem


class ComplaintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Complaint
        fields = ('item', 'reason',)

    def validate(self, attrs):
        attrs['user'] = self.context['request'].user
        return attrs


class SuggestItemSerializer(serializers.ModelSerializer):
    images = SmallImageSerializer(many=True)

    class Meta:
        model = ShopItem
        fields = ('id', 'name', 'images',)
