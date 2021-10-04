from rest_framework import serializers

from organizations.models import Partnership, Organization
from organizations.serializers.organization_serializers import PartnerSerializer


class PartnershipRequestSerializer(serializers.ModelSerializer):
    partnership_id = serializers.IntegerField(required=False, default=None)
    accepted_by = serializers.PrimaryKeyRelatedField(required=False, default=None, queryset=Organization.objects.all())
    requested_by = serializers.PrimaryKeyRelatedField(required=False, default=None, queryset=Organization.objects.all())

    class Meta:
        model = Partnership
        fields = ('requested_by', 'accepted_by', 'partnership_id')


class PartnershipSerializer(serializers.ModelSerializer):
    partner = serializers.SerializerMethodField()
    is_incoming = serializers.SerializerMethodField()

    def get_is_incoming(self, partnership: Partnership) -> bool:
        return partnership.accepted_by.id == self.context['organization_id']

    def get_partner(self, partnership: Partnership):
        if partnership.accepted_by.id == self.context['organization_id']:
            partner = partnership.requested_by
        else:
            partner = partnership.accepted_by

        return PartnerSerializer(partner, context={'request': self.context.get('request')}).data

    class Meta:
        model = Partnership
        fields = ('id', 'is_accepted', 'is_incoming', 'partner',)


class PartnershipDetailedSerializer(PartnershipSerializer):
    requested_by = PartnerSerializer()

    class Meta:
        model = Partnership
        fields = (
            'id',
            'can_check_attendance', 'can_see_stats', 'can_edit_organization',
            'can_share_cashback', 'can_share_cumulative', 'can_share_items',
            'requested_by',
        )


class PartnershipUpdateSerializer(serializers.ModelSerializer):
    can_check_attendance = serializers.BooleanField(required=False)
    can_see_stats = serializers.BooleanField(required=False)
    can_edit_organization = serializers.BooleanField(required=False)
    can_share_cashback = serializers.BooleanField(required=False)
    can_share_cumulative = serializers.BooleanField(required=False)
    can_share_items = serializers.BooleanField(required=False)

    class Meta:
        model = Partnership
        fields = (
            'can_check_attendance', 'can_see_stats', 'can_edit_organization',
            'can_share_cashback', 'can_share_cumulative', 'can_share_items',
        )
