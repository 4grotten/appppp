from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from common.exceptions import NotAcceptableException
from common.models import File
from common.serializers import ImageSerializer
from organizations.models import Organization, DiscountCard
from organizations.serializers.organization_serializers import (
    OrganizationUserTransactionSerializer, OrganizationShortInfoWithCurrencySerializer,
)
from organizations.services.organization_services import OrganizationService
from shop.models import Cart, Booking, ShopItem, Ticket
from shop.serializers.cart_serializers import CartSerializer, DeliveryInfoSerializer
from shop.serializers.item_serializers import TransactionBookingInfoSerializer, IsActiveBookingSerializer, \
    TicketPeriodSerializer, IsActiveTicketSerializer, TicketWithTicketPeriodSerializer
from transactions.models import Transaction, PayoutSystem, Recipient, Balance
from users.models import User
from users.serializers import ProfileBriefWithPhotoSerializer, UserInfoSerializer
from transactions.constants import DECLINED_RENTAL_OFFLINE_PAYMENT_TYPE, RENTAL_ICON_MAP, TICKET_ICON_MAP, \
    DECLINED_TICKET_OFFLINE_PAYMENT_TYPE, PRODUCT_ICON_MAP, DECLINED_PRODUCT_OFFLINE_PAYMENT_TYPE, WITHDRAWAL_ICON_MAP, \
    DECLINED_WITHDRAWAL_TYPE


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


class CompleteBookingSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)
    source_card = serializers.PrimaryKeyRelatedField(queryset=DiscountCard.objects.filter(is_published=True),
                                                     default=None, allow_null=True)
    discount_percent = serializers.IntegerField(required=True, validators=[MinValueValidator(0)])
    original_amount = serializers.DecimalField(max_digits=16, decimal_places=2,
                                               validators=[MinValueValidator(0)])
    from_cashback = serializers.DecimalField(max_digits=16, decimal_places=2, default=0,
                                             validators=[MinValueValidator(0)])
    booking = serializers.PrimaryKeyRelatedField(
        queryset=Booking.objects.filter(is_open=True), allow_null=True, required=False)

    class Meta:
        model = Transaction
        fields = (
            'transaction_id', 'original_amount', 'discount_percent', 'source_card', 'from_cashback',
            'booking',
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
    purchase_type = serializers.SerializerMethodField()
    icon_type = serializers.SerializerMethodField()


    def get_display_time(self, transaction: Transaction):
        if transaction.display_time is not None:
            return transaction.display_time.replace(tzinfo=None, second=0, microsecond=0)
        return None

    def get_purchase_type(self, transaction: Transaction):
        booking = Booking.objects.filter(transaction=transaction)
        if booking.exists():
            return ShopItem.RENTAL
        ticket = Ticket.objects.filter(transaction=transaction)
        if ticket.exists():
            return ShopItem.TICKET
        return ShopItem.PRODUCT

    def get_icon_type(self, transaction: Transaction):
        if transaction.type == Transaction.WITHDRAWAL:
            return WITHDRAWAL_ICON_MAP.get((transaction.type, transaction.status), DECLINED_WITHDRAWAL_TYPE)
        purchase_type = self.get_purchase_type(transaction)
        if purchase_type == ShopItem.PRODUCT:
            return PRODUCT_ICON_MAP.get((transaction.type, transaction.status, transaction.payment_status,
                                         transaction.delivery_type), DECLINED_PRODUCT_OFFLINE_PAYMENT_TYPE)
        if purchase_type == ShopItem.RENTAL:
            return RENTAL_ICON_MAP.get((transaction.type, transaction.status, transaction.payment_status),
                                       DECLINED_RENTAL_OFFLINE_PAYMENT_TYPE)
        return TICKET_ICON_MAP.get((transaction.type, transaction.status, transaction.payment_status,
                                    transaction.delivery_type), DECLINED_TICKET_OFFLINE_PAYMENT_TYPE)



    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback',
            'final_amount', 'updated_at', 'created_at', 'display_time', 'type', 'status', 'delivery_info',
            'payment_status', 'purchase_type', 'icon_type'
        )


class TransactionsTicketSerializer(serializers.ModelSerializer):
    display_time = serializers.SerializerMethodField()
    delivery_info = DeliveryInfoSerializer()
    purchase_type = serializers.SerializerMethodField()
    icon_type = serializers.SerializerMethodField()


    def get_display_time(self, transaction: Transaction):
        if transaction.display_time is not None:
            return transaction.display_time.replace(tzinfo=None, second=0, microsecond=0)
        return None

    def get_purchase_type(self, transaction: Transaction):
        return ShopItem.TICKET

    def get_icon_type(self, transaction: Transaction):
        return TICKET_ICON_MAP.get((transaction.type, transaction.status, transaction.payment_status,
                                    transaction.delivery_type), DECLINED_TICKET_OFFLINE_PAYMENT_TYPE)

    class Meta:
        model = Transaction
        fields = (
            'id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback',
            'final_amount', 'updated_at', 'created_at', 'display_time', 'type', 'status', 'delivery_info',
            'payment_status', 'purchase_type', 'icon_type'
        )


class OnlineCompleteSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)
    utc_offset_minutes = serializers.IntegerField(min_value=-720, max_value=840)

    class Meta:
        model = Transaction
        fields = ('transaction_id', 'utc_offset_minutes',)


class OnlineOfflinePaymentCompleteSerializer(serializers.ModelSerializer):
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
            'current_user_can_see_stats', 'delivery_info', 'payment_status'
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
            'payment_status', 'current_user_can_see_stats', 'delivery_info', 'organization'
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


class OrganizationRentalTransactionWithClientSerializer(TransactionDetailSerializer):
    client = ProfileBriefWithPhotoSerializer()
    organization = OrganizationShortInfoWithCurrencySerializer()
    current_user_can_see_stats = serializers.SerializerMethodField()
    booking = TransactionBookingInfoSerializer()

    def get_current_user_can_see_stats(self, instance):
        return OrganizationService.user_can_see_stats(user=self.context['request'].user,
                                                      organization=instance.organization)

    class Meta:
        model = Transaction
        fields = (
            'id', 'client', 'type', 'current_user_can_see_stats', 'organization', 'booking'
        )


class OrganizationTicketWithClientSerializer(TransactionDetailSerializer):
    client = ProfileBriefWithPhotoSerializer(source='user')
    organization = OrganizationShortInfoWithCurrencySerializer()
    item = TicketWithTicketPeriodSerializer()
    current_user_can_see_stats = serializers.SerializerMethodField()
    activated_time = serializers.SerializerMethodField()

    def get_current_user_can_see_stats(self, instance):
        return OrganizationService.user_can_see_stats(user=self.context['request'].user,
                                                      organization=instance.organization)

    def get_activated_time(self, ticket: Ticket):
        if ticket.is_active:
            return ticket.updated_at
        return None


    class Meta:
        model = Ticket
        fields = ('id', 'client', 'item', 'current_user_can_see_stats', 'organization', 'is_active', 'activated_time')


class StartEndDateTransactionSerializer(serializers.Serializer):
    start = serializers.DateField(required=False)
    end = serializers.DateField(required=False)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True),
                                                      default=None)
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all(), default=None)


class UserInfoBookingSerializer(serializers.Serializer):
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))
    booking = serializers.PrimaryKeyRelatedField(queryset=Booking.objects.all())


class UserInfoTicketSerializer(serializers.Serializer):
    client = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True), required=False)
    item = serializers.PrimaryKeyRelatedField(queryset=ShopItem.objects.all())


class ActivateTransactionWithClientSerializer(TransactionDetailSerializer):
    client = UserInfoSerializer()
    icon_type = serializers.SerializerMethodField()
    booking = IsActiveBookingSerializer()

    def get_icon_type(self, transaction: Transaction):
        return RENTAL_ICON_MAP.get((transaction.type, transaction.status, transaction.payment_status), DECLINED_RENTAL_OFFLINE_PAYMENT_TYPE)

    class Meta:
        model = Transaction
        fields = ('id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback',
                  'final_amount', 'client', 'type', 'status', 'icon_type', 'booking', 'created_at', 'updated_at')


class ActivateTransactionTicketWithClientSerializer(TransactionDetailSerializer):
    client = UserInfoSerializer()
    ticket = IsActiveTicketSerializer(many=True)

    class Meta:
        model = Transaction
        fields = ('id', 'currency', 'original_amount', 'discount_percent', 'savings', 'from_cashback', 'to_cashback',
                  'final_amount', 'client', 'type', 'status', 'created_at', 'updated_at', 'ticket')


class TransactionActivateSerializer(serializers.Serializer):
    transaction = serializers.PrimaryKeyRelatedField(queryset=Transaction.objects.filter(is_processed=True))


class TicketSerializer(serializers.Serializer):
    ticket = serializers.PrimaryKeyRelatedField(queryset=Ticket.objects.all())


class TicketActivateSerializer(serializers.Serializer):
    ticket = serializers.PrimaryKeyRelatedField(queryset=Ticket.objects.filter(is_active=False))


class ResultURLSerializer(serializers.Serializer):
    pg_order_id = serializers.CharField(required=False)
    pg_payment_id = serializers.CharField(required=False)
    pg_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    pg_currency = serializers.CharField(required=False)
    pg_net_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    pg_ps_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    pg_ps_full_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    pg_ps_currency = serializers.CharField(required=False)
    pg_description = serializers.CharField(required=False)
    pg_result = serializers.IntegerField(required=False)
    pg_payment_date = serializers.DateTimeField(required=False)
    pg_can_reject = serializers.IntegerField(required=False)
    pg_user_phone = serializers.CharField(required=False)
    pg_user_contact_email = serializers.EmailField(required=False)
    pg_need_email_notification = serializers.IntegerField(required=False)
    pg_testing_mode = serializers.IntegerField(required=False)
    pg_captured = serializers.IntegerField(required=False)
    pg_card_pan = serializers.CharField(required=False)
    pg_salt = serializers.CharField(required=False)
    pg_sig = serializers.CharField(required=False)
    pg_payment_method = serializers.CharField(required=False)
    user_id = serializers.CharField(required=False)
    purchase_type = serializers.CharField(required=False)


class PaymentSuccessSerializer(serializers.Serializer):
    pg_order_id = serializers.CharField(required=False)
    pg_payment_id = serializers.IntegerField(required=False)
    pg_error_code = serializers.CharField(required=False)
    pg_error_description = serializers.CharField(required=False)


class PayoutSystemSerializer(serializers.ModelSerializer):
    image = ImageSerializer()

    class Meta:
        model = PayoutSystem
        fields = ('id', 'name', 'image', 'fee_percent')


class RecipientSerializer(serializers.ModelSerializer):
    payout_system = PayoutSystemSerializer()
    image = ImageSerializer()

    class Meta:
        model = Recipient
        fields = ('id', 'payout_system', 'image', 'owner_name', 'card_number', 'transfer_amount')


class RecipientGeneralSerializer(serializers.ModelSerializer):
    payout_system = PayoutSystemSerializer()
    image = ImageSerializer()

    class Meta:
        model = Recipient
        fields = ('id', 'payout_system', 'image', 'owner_name', 'card_number', 'swift_bic_code', 'iban_account_number',
                  'country', 'city', 'address', 'postcode', 'email', 'transfer_amount')


class RecipientSwiftSerializer(serializers.ModelSerializer):
    payout_system = PayoutSystemSerializer()
    image = ImageSerializer()

    class Meta:
        model = Recipient
        fields = ('id', 'payout_system', 'image', 'owner_name', 'swift_bic_code', 'iban_account_number', 'country',
                  'city', 'address', 'postcode', 'email', 'transfer_amount')


class BalanceQueryParamSerializer(serializers.Serializer):
    balance = serializers.PrimaryKeyRelatedField(queryset=Balance.objects.all())
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))


class TransactionWithdrawalSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    payout_system = serializers.PrimaryKeyRelatedField(queryset=PayoutSystem.objects.all())
    balance = serializers.PrimaryKeyRelatedField(queryset=Balance.objects.all())
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), required=False, allow_null=True
    )
    owner_name = serializers.CharField(max_length=255)
    card_number = serializers.CharField(max_length=16)
    transfer_amount = serializers.DecimalField(max_digits=16, decimal_places=2)
    utc_offset_minutes = serializers.IntegerField(required=False)

    def validate_transfer_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Transfer amount must be greater than zero.")
        return value


class TransactionWithdrawalSwiftSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    balance = serializers.PrimaryKeyRelatedField(queryset=Balance.objects.all())
    image_id = serializers.PrimaryKeyRelatedField(
        queryset=File.objects.all(), required=False, allow_null=True
    )
    owner_name = serializers.CharField(max_length=255)
    swift_bic_code = serializers.CharField(max_length=11)
    iban_account_number = serializers.CharField(max_length=34)
    country = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=255)
    address = serializers.CharField()
    postcode = serializers.CharField(max_length=20)
    email = serializers.EmailField()
    transfer_amount = serializers.DecimalField(max_digits=16, decimal_places=2)
    utc_offset_minutes = serializers.IntegerField(required=False)

    def validate_transfer_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Transfer amount must be greater than zero.")
        return value


class TransactionWithdrawalDetailSerializer(serializers.ModelSerializer):
    display_time = serializers.SerializerMethodField()
    icon_type = serializers.SerializerMethodField()
    recipient_info = serializers.JSONField(source='fixed_cart')
    processed_by = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()
    employee_avatar = serializers.SerializerMethodField()
    employee_role = serializers.SerializerMethodField()

    def get_employee_avatar(self, instance):
        if not instance.processed_by:
            return None
        return ImageSerializer(
            instance.employee_avatar,
            context={"request": self.context.get("request")}
        ).data

    def get_employee_name(self, instance):
        if not instance.processed_by:
            return None
        return instance.employee_name

    def get_processed_by(self, instance):
        if not instance.processed_by:
            return None
        return instance.processed_by.id

    def get_employee_role(self, instance):
        if not instance.processed_by:
            return None
        return instance.employee_role

    def get_display_time(self, transaction: Transaction):
        if transaction.display_time is not None:
            return transaction.display_time.replace(tzinfo=None, second=0, microsecond=0)
        return None

    def get_icon_type(self, transaction: Transaction):
        return WITHDRAWAL_ICON_MAP.get((transaction.type, transaction.status), DECLINED_WITHDRAWAL_TYPE)

    class Meta:
        model = Transaction
        fields = (
            'id', 'processed_by', 'employee_name', 'employee_avatar', 'employee_role', 'currency', 'original_amount',
            'discount_percent', 'savings', 'from_cashback', 'to_cashback', 'final_amount', 'updated_at', 'created_at',
            'display_time', 'type', 'status', 'icon_type', 'withdrawal_type', 'recipient_info')


class SwiftPaymentCompleteSerializer(serializers.ModelSerializer):
    transaction_id = serializers.IntegerField(required=True)

    class Meta:
        model = Transaction
        fields = ('transaction_id',)


class BalanceSerializer(serializers.ModelSerializer):
    payout_systems = PayoutSystemSerializer(many=True)

    class Meta:
        model = Balance
        fields = ('id', 'organization', 'currency', 'balance_amount', 'payout_systems')


class BalanceWithUnprocessedTransactionCountSerializer(serializers.ModelSerializer):
    payout_systems = PayoutSystemSerializer(many=True)
    unprocessed_transaction_count = serializers.SerializerMethodField()

    def get_unprocessed_transaction_count(self, balance: Balance):
        return Transaction.objects.filter(payment_info__id=balance.id, status=Transaction.IN_PROGRESS,
                                          type=Transaction.WITHDRAWAL).count()

    class Meta:
        model = Balance
        fields = ('id', 'organization', 'currency', 'balance_amount', 'payout_systems', 'unprocessed_transaction_count')

class BalanceInTransactionSerializer(serializers.ModelSerializer):
    payout_systems = PayoutSystemSerializer(many=True)

    class Meta:
        model = Balance
        fields = ('id', 'organization', 'currency', 'payout_systems')
