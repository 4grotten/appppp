from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.db import models

from applications.models import UserApp
from common.models import Currency, TimestampModel
from common.utils import DecimalEncoder, DecimalDecoder, upload_file_with_unique_name
from organizations.models import Organization, DiscountCard
from users.models import User


class TransactionFile(TimestampModel):
    order = models.PositiveSmallIntegerField(default=0, editable=False)
    file = models.FileField(upload_to=upload_file_with_unique_name,
                             help_text=_('File that you want to store'),
                             null=True, blank=True)

    @property
    def name(self):
        return self.file.name.split("/")[-1]

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        super(TransactionFile, self).save()

    class Meta:
        ordering = ('order',)


class Transaction(TimestampModel):
    FIXED = 'fixed'
    CUMULATIVE = 'cumulative'
    CASHBACK = 'cashback'
    MANUAL = 'manual'
    DISCOUNT_TYPES = (
        (FIXED, FIXED),
        (CUMULATIVE, CUMULATIVE),
        (CASHBACK, CASHBACK),
        (MANUAL, MANUAL),
    )

    ONLINE = 'online'
    OFFLINE = 'offline'
    WITHDRAWAL = 'withdrawal'
    ASSISTANT = 'assistant'
    ORG_SUBSCRIPTION = 'org_subscription'
    USER_APP = 'user_app'
    TYPE = (
        (ONLINE, ONLINE),
        (OFFLINE, OFFLINE),
        (WITHDRAWAL, WITHDRAWAL),
        (ASSISTANT, ASSISTANT),
        (ORG_SUBSCRIPTION, ORG_SUBSCRIPTION),
        (USER_APP, USER_APP)
    )

    BANKCARD = 'bankcard'
    SWIFT = 'swift'

    WITHDRAWAL_TYPES = (
        (BANKCARD, BANKCARD),
        (SWIFT, SWIFT)
    )

    CASH_COURIER = 'cash_courier'
    SELF_PICKUP = 'self_pickup'
    CART_CHECKOUT = 'cart_checkout'
    ONLINE_PAYMENT = 'online_payment'

    DELIVERY_TYPE = (
        (CASH_COURIER, CASH_COURIER),
        (SELF_PICKUP, SELF_PICKUP),
        (CART_CHECKOUT, CART_CHECKOUT),
        (ONLINE_PAYMENT, ONLINE_PAYMENT),
    )

    REJECTED = 'rejected'
    IN_PROGRESS = 'in_progress'
    UNDER_REVIEW = 'under_review'
    ACCEPTED_WITHDRAWAL = 'accepted_withdrawal'
    ACCEPTED = 'accepted'
    REFUNDED = 'refunded'
    ERROR = 'error'

    STATUS = (
        (IN_PROGRESS, IN_PROGRESS),
        (UNDER_REVIEW, UNDER_REVIEW),
        (ACCEPTED_WITHDRAWAL, ACCEPTED_WITHDRAWAL),
        (ACCEPTED, ACCEPTED),
        (REJECTED, REJECTED),
        (ERROR, ERROR)
    )

    PAYMENT_STATUS = (
        (IN_PROGRESS, IN_PROGRESS),
        (ACCEPTED, ACCEPTED),
        (REJECTED, REJECTED),
        (REFUNDED, REFUNDED),
    )

    client = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bought_transactions', null=True)
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='processed_transactions', null=True)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, null=True, related_name='transactions')
    user_app = models.ForeignKey(UserApp, on_delete=models.PROTECT, null=True, related_name='transactions')

    employee_name = models.CharField(max_length=255, null=True, blank=True)
    employee_role = models.CharField(max_length=255, null=True)
    employee_avatar = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)

    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='transactions', default='KGS')
    original_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    final_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0, editable=False,
                                       validators=[MinValueValidator(0)])
    discount_percent = models.PositiveSmallIntegerField(default=0)
    fee_percent = models.PositiveSmallIntegerField(default=0)
    fee_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    savings = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    from_cashback = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    to_cashback = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    fixed_cart = models.JSONField(null=True, encoder=DecimalEncoder, decoder=DecimalDecoder)
    payment_info = models.JSONField(null=True, encoder=DecimalEncoder, decoder=DecimalDecoder)

    withdrawal_type = models.CharField(choices=WITHDRAWAL_TYPES, max_length=20, default=BANKCARD)

    discount_type = models.CharField(choices=DISCOUNT_TYPES, max_length=20, default=MANUAL)
    type = models.CharField(choices=TYPE, max_length=20, default=OFFLINE)
    payment_status = models.CharField(choices=PAYMENT_STATUS, max_length=20, default=IN_PROGRESS)
    delivery_type = models.CharField(choices=DELIVERY_TYPE, max_length=20, default=SELF_PICKUP)
    source_card = models.ForeignKey(DiscountCard, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='transactions')
    is_processed = models.BooleanField(default=False)
    status = models.CharField(choices=STATUS, max_length=20, default=IN_PROGRESS)
    purchase_id = models.PositiveSmallIntegerField(null=True, blank=True)

    files = models.ManyToManyField(TransactionFile, blank=True, related_name='transactions')
    order_comment = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    display_time = models.DateTimeField(null=True)

    def __str__(self):  # pragma: no cover
        return f'Transaction #{self.id} for {self.original_amount}'

    class Meta:
        ordering = ('-updated_at',)

    def save(self, *args, **kwargs):
        self.final_amount = self.original_amount - self.savings - self.from_cashback - self.fee_amount
        super().save(*args, **kwargs)


class PayoutSystem(models.Model):
    name = models.CharField(max_length=255)
    image = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)
    fee_percent = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.name

class Recipient(models.Model):
    payout_system = models.ForeignKey(PayoutSystem, on_delete=models.PROTECT, related_name='recipients')
    image = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)

    owner_name = models.CharField(max_length=255, null=True, blank=True)
    card_number = models.CharField(max_length=16, null=True, blank=True)

    swift_bic_code = models.CharField(max_length=11, null=True, blank=True)
    iban_account_number = models.CharField(max_length=34, null=True, blank=True)
    country = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    postcode = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)


    transfer_amount = models.DecimalField(max_digits=16, decimal_places=2)

    def __str__(self):
        return f"Recipient {self.owner_name} using {self.payout_system}"


class Balance(models.Model):
    KGS = 'KGS'
    TRC = 'TRC20'
    CURRENCY = (
        (KGS, KGS),
        (TRC, TRC)
    )
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='balances')
    currency = models.CharField(max_length=20, choices=CURRENCY, default=KGS)
    balance_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0, editable=False)
    payout_systems = models.ManyToManyField(PayoutSystem)

    def __str__(self):
        return f"Balance for {self.organization}"
