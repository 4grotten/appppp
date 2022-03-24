from rest_framework import serializers

from organizations.models import Subscription


class LocationSerializer(serializers.Serializer):
    address = serializers.CharField()
    longitude = serializers.FloatField(allow_null=True)
    latitude = serializers.FloatField(allow_null=True)


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('organization',)


class AcceptFollowerSerializer(serializers.ModelSerializer):

    def get_unique_together_validators(self):
        """Overriding method to disable unique together checks"""
        return []

    class Meta:
        model = Subscription
        fields = ('organization', 'user')
