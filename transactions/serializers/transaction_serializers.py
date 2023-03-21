from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from common.exceptions import NotAcceptableException
from common.serializers import ImageSerializer
from organizations.models import Organization, DiscountCard
from organizations.serializers.organization_serializers import (
    OrganizationUserTransactionSerializer, OrganizationShortInfoWithCurrencySerializer,
)
from organizations.services.organization_services import OrganizationService
from shop.models import Cart, Booking
from shop.serializers.cart_serializers import CartSerializer, DeliveryInfoSerializer, BookingSerializer
from shop.serializers.item_serializers import TransactionBookingInfoSerializer, ItemRentalRetrieveSerializer
from transactions.models import Transaction
from users.models import User
from users.serializers import ProfileBriefWithPhotoSerializer


class OffsetUTCSerializer(serializers.Serializer):
    utc_offset_minutes = serializers.IntegerField(min_value=-720, max_value=840)


class PreprocessSerializer(serializers.Serializer):
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all())
    cart = serializers.PrimaryKeyRelatedField(
        queryset=Cart.objects.filter(is_open=True), allow_null=True, required=False)


class CompleteSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)
    source_card = serializers.PrimaryKeyRelatedField(queryset=DiscountCard.objects.filter(is_published=True),
                                                     default=None, allow_null=True)
    discount_percent = serializers.IntegerField(required=True, validators=[MinValueValidator(0)])
    original_amount = serializers.DecimalField(max_digits=16, decimal_places=2,
                                               validators=[MinValueValidator(0)])
    from_cashback = serializers.DecimalField(max_digits=16, decimal_places=2, default=0,
                                             validators=[MinValueValidator(0)])
    cart = serializers.PrimaryKeyRelatedField(
        queryset=Cart.objects.filter(is_open=True), allow_null=True, required=False)
    utc_offset_minutes = serializers.IntegerField(min_value=-720, max_value=840)

    class Meta:
        model = Transaction
        fields = (
            'transaction_id', 'original_amount', 'discount_percent', 'source_card', 'from_cashback',
            'cart', 'utc_offset_minutes',
        )

    def validate(self, attrs):
        original_amount = attrs['original_amount']
        from_cashback = attrs['from_cashback']

        if from_cashback > original_amount:
            raise NotAcceptableException(_('Cashback amount is greater than original amount'))

        card = attrs['source_card']
        percent = attrs['discount_percent']

        if card is not None and not card.percent == percent:
            raise NotAcceptableException(_('Discount percent does not match with cards percent'))

        return attrs


class TransactionsSerializer(serializers.ModelSerializer):
    display_time = serializers.SerializerMethodField()
    delivery_info = DeliveryInfoSerializer()

    def get_display_time(self, transaction: Transaction):
        if transaction.display_time is not None:
            return transaction.display_time.replace(tzinfo=None, second=0, microsecond=0)
        return None

    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback',
            'final_amount', 'updated_at', 'created_at', 'display_time', 'type', 'status', 'delivery_info',
            'payment_status'
        )


class OnlineCompleteSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)
    utc_offset_minutes = serializers.IntegerField(min_value=-720, max_value=840)

    class Meta:
        model = Transaction
        fields = ('transaction_id', 'utc_offset_minutes',)


class OnlinePaymentCompleteSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)

    class Meta:
        model = Transaction
        fields = ('transaction_id',)


class TransactionDetailSerializer(serializers.ModelSerializer):
    organization = OrganizationUserTransactionSerializer()
    employee_avatar = ImageSerializer()
    cart = serializers.SerializerMethodField()
    current_user_can_see_stats = serializers.SerializerMethodField()
    delivery_info = DeliveryInfoSerializer()
    display_time = serializers.SerializerMethodField()

    def get_display_time(self, transaction: Transaction):
        if transaction.display_time is not None:
            return transaction.display_time.replace(tzinfo=None, second=0, microsecond=0)
        return None

    def get_cart(self, instance: Transaction):
        if instance.fixed_cart:
            return instance.fixed_cart
        try:
            cart = instance.cart
        except Cart.DoesNotExist:
            return None
        return CartSerializer(instance=cart, context=self.context).data

    def get_current_user_can_see_stats(self, instance):
        return OrganizationService.user_can_see_stats(user=self.context.get('user'),
                                                      organization=instance.organization)

    class Meta:
        model = Transaction
        fields = (
            'id', 'purchase_id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback',
            'to_cashback', 'final_amount', 'processed_by', 'employee_name', 'employee_avatar', 'employee_role',
            'updated_at', 'created_at', 'display_time', 'organization', 'delivery_type', 'type', 'cart', 'status',
            'current_user_can_see_stats', 'delivery_info'
        )


class TransactionWithClientSerializer(TransactionDetailSerializer):
    client = ProfileBriefWithPhotoSerializer()
    cart = serializers.SerializerMethodField()
    delivery_info = DeliveryInfoSerializer()
    processed_by = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    employee_avatar = serializers.SerializerMethodField()
    employee_role = serializers.SerializerMethodField()
    organization = OrganizationShortInfoWithCurrencySerializer()
    current_user_can_see_stats = serializers.SerializerMethodField()

    def get_cart(self, instance: Transaction):
        if instance.fixed_cart:
            return instance.fixed_cart
        try:
            cart = instance.cart
        except Cart.DoesNotExist:
            return None
        return CartSerializer(instance=cart, context=self.context).data

    def get_employee_avatar(self, instance):
        if not instance.processed_by and OrganizationService.user_can_see_stats(
                user=self.context['request'].user,
                organization=instance.organization
        ):
            return ImageSerializer(self.context['request'].user.avatar).data

        return ImageSerializer(
            instance.employee_avatar,
            context={"request": self.context.get("request")}
        ).data

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
            'id', 'purchase_id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback',
            'to_cashback', 'final_amount', 'processed_by', 'employee_name', 'employee_avatar', 'employee_role',
            'updated_at', 'created_at', 'display_time', 'client', 'delivery_type', 'type', 'cart', 'status',
            'current_user_can_see_stats', 'delivery_info', 'organization'
        )


class BookingTransactionWithClientSerializer(TransactionDetailSerializer):
    client = ProfileBriefWithPhotoSerializer()
    processed_by = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    employee_avatar = serializers.SerializerMethodField()
    employee_role = serializers.SerializerMethodField()
    organization = OrganizationShortInfoWithCurrencySerializer()
    current_user_can_see_stats = serializers.SerializerMethodField()
    booking = TransactionBookingInfoSerializer()


    def get_employee_avatar(self, instance):
        if not instance.processed_by and OrganizationService.user_can_see_stats(
                user=self.context['request'].user,
                organization=instance.organization
        ):
            return ImageSerializer(self.context['request'].user.avatar).data

        return ImageSerializer(
            instance.employee_avatar,
            context={"request": self.context.get("request")}
        ).data

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
        elif not instance.processed_by:
            return None
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
            'id', 'purchase_id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback',
            'to_cashback', 'final_amount', 'processed_by', 'employee_name', 'employee_avatar', 'employee_role',
            'updated_at', 'created_at', 'display_time', 'client', 'type', 'current_user_can_see_stats', 'organization',
            'booking', 'status', 'payment_status'
        )


class StartEndDateTransactionSerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True),
                                                      default=None)
