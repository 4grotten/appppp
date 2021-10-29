from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from organizations.models import Partnership, Organization
from organizations.serializers.organization_serializers import PartnerSerializer


class PartnershipRequestSerializer(serializers.ModelSerializer):
    partnership_id = serializers.IntegerField(required=False, default=None)
    accepted_by = serializers.PrimaryKeyRelatedField(required=False, default=None, queryset=Organization.objects.all())
    requested_by = serializers.PrimaryKeyRelatedField(required=False, default=None, queryset=Organization.objects.all())

    def validate(self, data):

        """ Check that if  partnership_id send, it send  without accepted_by and requested_by, but
         when accepted_by and requested_by send, they send together and without partnership_id."""

        if not data['partnership_id']:
            if (data['accepted_by'] and not data['requested_by'])\
                    or (data['requested_by'] and not data['accepted_by']):
                raise NotAcceptableException(_("If one of the - requested_by or accepted_by fields is sent,"
                                               " the second field is also required"))

        if data['partnership_id'] and (data['accepted_by'] or data['requested_by']):
            raise NotAcceptableException(_("The request must contain fields or"
                                           " requested_by and accepted_by or only partnerships_id"))

        if not data['partnership_id'] and not (data['accepted_by'] or data['requested_by']):
            raise NotAcceptableException(_("The request must contain fields or"
                                           " requested_by and accepted_by or only partnerships_id"))

        if data['accepted_by'] and data['requested_by'] and data['accepted_by'] == data['requested_by']:
            raise NotAcceptableException(_("You cannot create a partnership for yourself"))

        return data

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
