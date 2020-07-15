from rest_framework import serializers

from common.exceptions import NotAcceptableException
from organizations.models import DiscountCard, Organization
from users.models import User
from .models import Transaction


class PreprocessSerializer(serializers.Serializer):
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())


class CompleteSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)
    source_card = serializers.PrimaryKeyRelatedField(queryset=DiscountCard.objects.filter(is_published=True),
                                                     allow_null=True)
    discount_percent = serializers.IntegerField(required=True)

    class Meta:
        model = Transaction
        fields = ('transaction_id', 'original_amount', 'savings', 'discount_percent', 'source_card')

    def validate(self, attrs):
        card = attrs['source_card']
        percent = attrs['discount_percent']

        if card is not None and not card.percent == percent:
            raise NotAcceptableException('Discount percent does not match with cards percent')

        calculated_savings = (attrs['original_amount'] * percent) / 100
        if not calculated_savings == attrs['savings']:
            raise NotAcceptableException('Savings are incorrectly calculated')

        return attrs
