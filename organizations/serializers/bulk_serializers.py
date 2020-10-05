from django.core.validators import MinValueValidator
from rest_framework import serializers

from organizations.constants import TYPES
from organizations.models import DiscountCard, Organization


class DiscountCardBulkDeleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCard
        fields = ('id',)


class DiscountCardBulkUpdateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=DiscountCard.objects.filter(is_published=True))
    percent = serializers.IntegerField(required=False)
    limit = serializers.DecimalField(required=False, allow_null=True,
                                     max_digits=16, decimal_places=2,
                                     validators=[MinValueValidator(0)])
    type = serializers.ChoiceField(choices=TYPES)


class BulkUpdateSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    cards = DiscountCardBulkUpdateSerializer(many=True)


class BulkDeleteSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    cards = serializers.PrimaryKeyRelatedField(many=True, queryset=DiscountCard.objects.filter(is_published=True))
