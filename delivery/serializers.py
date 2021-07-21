from rest_framework import serializers


class DeliveryAllItemsCountSerializer(serializers.Serializer):
    count = serializers.IntegerField()
