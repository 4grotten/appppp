from django.core.validators import MinValueValidator
from django.db import models

from common.models import Currency, TimestampModel
from common.utils import DecimalEncoder, DecimalDecoder
from organizations.models import Organization, DiscountCard
from users.models import User


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
    TYPE = (
        (ONLINE, ONLINE),
        (OFFLINE, OFFLINE),
    )

    CASH_COURIER = 'cash_courier'
    SELF_PICKUP = 'self_pickup'

    DELIVERY_TYPE = (
        (CASH_COURIER, CASH_COURIER),
        (SELF_PICKUP, SELF_PICKUP)
    )

    REJECTED = 'rejected'
    IN_PROGRESS = 'in_progress'
    ACCEPTED = 'accepted'
    STATUS = (
        (IN_PROGRESS, IN_PROGRESS),
        (ACCEPTED, ACCEPTED),
        (REJECTED, REJECTED)
    )

    client = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bought_transactions')
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='processed_transactions', null=True)
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='transactions')

    employee_name = models.CharField(max_length=255, null=True, blank=True)
    employee_role = models.CharField(max_length=255, null=True)
    employee_avatar = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)

    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='transactions', default='KGS')
    original_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount_percent = models.PositiveSmallIntegerField(default=0)
    savings = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    from_cashback = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    to_cashback = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0, editable=False,
                                       validators=[MinValueValidator(0)])
    fixed_cart = models.JSONField(null=True, encoder=DecimalEncoder, decoder=DecimalDecoder)

    discount_type = models.CharField(choices=DISCOUNT_TYPES, max_length=20, default=MANUAL)
    type = models.CharField(choices=TYPE, max_length=20, default=OFFLINE)
    delivery_type = models.CharField(choices=DELIVERY_TYPE, max_length=20, default=SELF_PICKUP)
    source_card = models.ForeignKey(DiscountCard, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='transactions')
    is_processed = models.BooleanField(default=False)
    status = models.CharField(choices=STATUS, max_length=20, default=IN_PROGRESS)

    def __str__(self):  # pragma: no cover
        return f'Transaction #{self.id} for {self.original_amount} in {self.organization.title}'

    class Meta:
        ordering = ('-updated_at',)

    def save(self, *args, **kwargs):
        self.final_amount = self.original_amount - self.savings - self.from_cashback
        super().save(*args, **kwargs)
