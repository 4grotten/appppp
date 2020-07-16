from rest_framework import serializers

from organizations.models import OrganizationClientFinancialStatus


class OwnedCumulativeCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationClientFinancialStatus
        fields = ('id',)
