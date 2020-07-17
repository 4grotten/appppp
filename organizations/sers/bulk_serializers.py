from rest_framework import serializers

from organizations.models import DiscountCard, Organization


class BulkUpdateSerializer(serializers.Serializer):
    pass


class DiscountCardIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountCard
        fields = ('id',)


class BulkDeleteSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    cards = serializers.PrimaryKeyRelatedField(many=True, queryset=DiscountCard.objects.filter(is_published=True))
