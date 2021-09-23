from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Service


class ServiceSerializer(serializers.ModelSerializer):
    icon = ImageSerializer()

    class Meta:
        model = Service
        fields = ('id', 'name', 'icon',)
