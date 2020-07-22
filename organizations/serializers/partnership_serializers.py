from rest_framework import serializers

from organizations.models import Partnership


class PartnershipRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partnership
        fields = ('requested_by', 'accepted_by',)
