from django.core.validators import MinValueValidator
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from organizations.models import Organization, DiscountCard
from organizations.serializers.organization_serializers import OrganizationUserTransactionSerializer
from organizations.services.organization_services import OrganizationService
from transactions.models import Transaction
from users.models import User
from users.serializers import ProfileBriefWithPhotoSerializer


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


class TransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'final_amount',
            'updated_at', 'created_at',
        )


class TransactionDetailSerializer(serializers.ModelSerializer):
    processed_by = ProfileBriefWithPhotoSerializer()
    employee_role = serializers.SerializerMethodField()
    organization = OrganizationUserTransactionSerializer()

    def get_employee_role(self, transaction: Transaction):
        return OrganizationService.get_user_role_in_organization(organization=transaction.organization,
                                                                 user=self.context['request'].user)

    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'final_amount',
            'updated_at', 'created_at', 'processed_by', 'employee_role', 'organization',
        )


class TransactionWithClientSerializer(TransactionDetailSerializer):
    client = ProfileBriefWithPhotoSerializer()

    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'final_amount',
            'updated_at', 'created_at', 'processed_by', 'employee_role', 'client',
        )


class StartEndDateTransactionSerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True),
                                                      default=None)
