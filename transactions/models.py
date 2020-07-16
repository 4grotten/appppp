from django.db import models

from common.models import Currency, TimestampModel
from organizations.models import Organization, DiscountCard
from users.models import User


class Transaction(TimestampModel):
    FIXED = 'fixed'
    CUMULATIVE = 'cumulative'
    MANUAL = 'manual'

    TYPES = (
        (FIXED, FIXED),
        (CUMULATIVE, CUMULATIVE),
        (MANUAL, MANUAL),
    )

    client = models.ForeignKey(User, on_delete=models.PROTECT, related_name='bought_transactions')
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='processed_transactions')
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='transactions')

    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='transactions', default='KGS')
    original_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.PositiveSmallIntegerField(default=0)
    savings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    discount_type = models.CharField(choices=TYPES, max_length=20, default=MANUAL)
    source_card = models.ForeignKey(DiscountCard, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='transactions')

    is_processed = models.BooleanField(default=False)

    def __str__(self):
        return f'Transaction #{self.id} for {self.original_amount} in {self.organization.title}'

    class Meta:
        ordering = ('-updated_at',)

    def save(self, *args, **kwargs):
        self.final_amount = self.original_amount - self.savings
        super().save(*args, **kwargs)
