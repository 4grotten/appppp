from django.core.validators import MinValueValidator
from rest_framework import serializers
from rest_framework.fields import CurrentUserDefault

from common.exceptions import NotAcceptableException
from common.serializers import ImageSerializer
from organizations.models import Organization, DiscountCard
from organizations.serializers.organization_serializers import OrganizationUserTransactionSerializer
from organizations.services.organization_services import OrganizationService
from shop.serializers.cart_serializers import CartWithItemsSerializer, CartSerializer, DeliveryInfoSerializer
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
    from_cashback = serializers.DecimalField(max_digits=16, decimal_places=2, default=0,
                                             validators=[MinValueValidator(0)])

    class Meta:
        model = Transaction
        fields = ('transaction_id', 'original_amount', 'discount_percent', 'source_card', 'from_cashback')

    def validate(self, attrs):
        original_amount = attrs['original_amount']
        from_cashback = attrs['from_cashback']

        if from_cashback > original_amount:
            raise NotAcceptableException('Cashback amount is greater than original amount')

        card = attrs['source_card']
        percent = attrs['discount_percent']

        if card is not None and not card.percent == percent:
            raise NotAcceptableException('Discount percent does not match with cards percent')

        return attrs


class TransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback',
            'final_amount', 'updated_at', 'created_at', 'type', 'status'
        )


class OnlineCompleteSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)
    from_cashback = serializers.DecimalField(max_digits=16, decimal_places=2, default=0,
                                             validators=[MinValueValidator(0)])

    class Meta:
        model = Transaction
        fields = ('transaction_id', 'from_cashback')


class TransactionDetailSerializer(serializers.ModelSerializer):
    organization = OrganizationUserTransactionSerializer()
    employee_avatar = ImageSerializer()
    cart = CartSerializer()
    current_user_can_see_stats = serializers.SerializerMethodField()
    delivery_info = DeliveryInfoSerializer()

    def get_current_user_can_see_stats(self, instance):
        return OrganizationService.user_can_see_stats(user=self.context.get('user'),
                                                      organization=instance.organization)

    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback',
            'final_amount', 'processed_by', 'employee_name', 'employee_avatar', 'employee_role',
            'updated_at', 'created_at', 'organization', 'delivery_type', 'type', 'cart', 'status',
            'current_user_can_see_stats', 'delivery_info'
        )


class TransactionWithClientSerializer(TransactionDetailSerializer):
    client = ProfileBriefWithPhotoSerializer()
    cart = CartSerializer()
    delivery_info = DeliveryInfoSerializer()
    processed_by = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    employee_avatar = serializers.SerializerMethodField()
    employee_role = serializers.SerializerMethodField()
    organization = OrganizationUserTransactionSerializer()
    current_user_can_see_stats = serializers.SerializerMethodField()

    def get_employee_avatar(self, instance):
        if not instance.processed_by and OrganizationService.user_can_see_stats(user=self.context['request'].user,
                                                                                organization=instance.organization):
            return ImageSerializer(self.context['request'].user.avatar).data
        return ImageSerializer(instance.employee_avatar).data

    def get_current_user_can_see_stats(self, instance):
        return OrganizationService.user_can_see_stats(user=self.context['request'].user,
                                                      organization=instance.organization)

    def get_employee_name(self, instance):
        if not instance.processed_by and OrganizationService.user_can_see_stats(user=self.context['request'].user,
                                                                                organization=instance.organization):
            return self.context['request'].user.full_name
        return instance.employee_name

    def get_processed_by(self, instance):
        if not instance.processed_by and OrganizationService.user_can_see_stats(user=self.context['request'].user,
                                                                                organization=instance.organization):
            return self.context['request'].user.id
        return instance.processed_by.id

    def get_employee_role(self, instance):
        if not instance.processed_by and OrganizationService.user_can_see_stats(user=self.context['request'].user,
                                                                                organization=instance.organization):
            return OrganizationService.get_user_role_in_organization(organization=instance.organization,
                                                                     user=self.context['request'].user)
        return instance.employee_role

    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback',
            'final_amount', 'processed_by', 'employee_name', 'employee_avatar', 'employee_role',
            'updated_at', 'created_at', 'client', 'delivery_type', 'type', 'cart', 'status',
            'current_user_can_see_stats', 'delivery_info', 'fixed_cart'
        )


class StartEndDateTransactionSerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True),
                                                      default=None)
