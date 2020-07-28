from django.core.validators import MinValueValidator
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from organizations.models import Organization, DiscountCard
from transactions.models import Transaction
from users.models import User
from users.serializers import ProfileSerializer


class PreprocessSerializer(serializers.Serializer):
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())


class CompleteSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)
    source_card = serializers.PrimaryKeyRelatedField(queryset=DiscountCard.objects.filter(is_published=True),
                                                     default=None, allow_null=True)
    discount_percent = serializers.IntegerField(required=True, validators=[MinValueValidator(0)])
    original_amount = serializers.DecimalField(max_digits=16, decimal_places=2,
                                               validators=[MinValueValidator(0)])

    class Meta:
        model = Transaction
        fields = ('transaction_id', 'original_amount', 'discount_percent', 'source_card')

    def validate(self, attrs):
        card = attrs['source_card']
        percent = attrs['discount_percent']

        if card is not None and not card.percent == percent:
            raise NotAcceptableException('Discount percent does not match with cards percent')

        return attrs


class UserTotalsSerializer(serializers.Serializer):
    total_original_amount = serializers.DecimalField(max_digits=16, decimal_places=2)
    total_savings = serializers.DecimalField(max_digits=16, decimal_places=2)


class TransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'original_amount', 'discount_percent', 'savings', 'created_at', 'currency')


class TransactionDetailSerializer(serializers.ModelSerializer):
    processed_by = ProfileSerializer(many=False)

    class Meta:
        model = Transaction
        fields = ('id', 'original_amount', 'discount_percent', 'savings', 'created_at', 'currency', 'processed_by')


class StartEndDateTransactionSerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
