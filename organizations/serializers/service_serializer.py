from rest_framework import serializers

from organizations.models import Service


class ServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Service
        fields = ['pk', 'name', 'icon', 'subcategory']
