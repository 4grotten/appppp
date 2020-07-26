from rest_framework import serializers

from organizations.models import Partnership
from organizations.serializers.organization_serializers import PartnerSerializer


class PartnershipRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partnership
        fields = ('requested_by', 'accepted_by',)


class PartnershipSerializer(serializers.ModelSerializer):
    accepted_by = PartnerSerializer()

    class Meta:
        model = Partnership
        fields = ('id', 'is_accepted', 'accepted_by',)


class PartnershipDetailedSerializer(PartnershipSerializer):
    class Meta:
        model = Partnership
        fields = ('id', 'is_accepted', 'can_check_attendance', 'can_see_stats', 'can_edit_organization', 'accepted_by',)


class PartnershipUpdateSerializer(serializers.ModelSerializer):
    can_check_attendance = serializers.BooleanField()
    can_see_stats = serializers.BooleanField()
    can_edit_organization = serializers.BooleanField()

    class Meta:
        model = Partnership
        fields = ('can_check_attendance', 'can_see_stats', 'can_edit_organization',)
