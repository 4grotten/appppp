from rest_framework import serializers

from organizations.models import Organization
from users.models import User


class ClientDiscountInfoSerializer(serializers.Serializer):
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
