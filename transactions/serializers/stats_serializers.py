from rest_framework import serializers


class StartEndDateSerializer(serializers.Serializer):
    start = serializers.DateField(required=True)
    end = serializers.DateField(required=True)


class PartnersTotalStatsSerializer(serializers.Serializer):
    total_spent = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_savings = serializers.DecimalField(max_digits=16, decimal_places=2)