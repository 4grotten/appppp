from rest_framework import serializers

from users.models import User


class StartEndDateSerializer(serializers.Serializer):
    start = serializers.DateField(default=None)
    end = serializers.DateField(default=None)


class StartEndProcessedByQueryParamSerializer(serializers.Serializer):
    start = serializers.DateField(default=None)
    end = serializers.DateField(default=None)
    processed_by = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), default=None)


class TotalStatsSerializer(serializers.Serializer):
    total_spent = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_savings = serializers.DecimalField(max_digits=16, decimal_places=2)
    currency = serializers.CharField()
