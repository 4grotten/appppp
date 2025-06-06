from decimal import Decimal

from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import TimestampModel, Currency
from users.models import User


class UserAppCategory(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = _('UserApp categories')
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}'


class UserAppType(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(UserAppCategory, on_delete=models.CASCADE, related_name='types')
    is_adult = models.BooleanField(default=False)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return f'{self.title}'


class UserAppBanner(TimestampModel):
    image = models.ForeignKey('common.File', on_delete=models.CASCADE, related_name='user_app_banners')
    is_default = models.BooleanField(default=False, help_text='Системный баннер, удаляется только из админки')

    class Meta:
        verbose_name = 'Баннер приложения'
        verbose_name_plural = 'Баннеры приложений'

    def __str__(self):
        return f"{'Default' if self.is_default else 'Custom'} banner {self.pk}"


class UserApp(TimestampModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_user_apps')
    title = models.CharField(max_length=255)
    title_lang = models.CharField(max_length=8, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    description_lang = models.CharField(max_length=8, null=True, blank=True)
    types = models.ManyToManyField(UserAppType, blank=True, related_name='user_apps')
    image = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='user_apps')
    banners = models.ManyToManyField(UserAppBanner, blank=True, related_name='user_apps')
    selected_banner = models.ForeignKey(UserAppBanner, null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='selected_for_user_apps',
                                        help_text="The banner shown on the UserApp's detail page"
                                        )
    app_images = models.ManyToManyField('common.File', blank=True, related_name='user_app_images')
    app_link = models.URLField()
    # Optional fields
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    instagram_link = models.URLField(null=True, blank=True)
    youtube_links = models.JSONField(null=True, blank=True)
    support_link = models.URLField(null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    terms_link = models.URLField(null=True, blank=True)


    def __str__(self):
        return self.title


class AddedApp(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="apps")
    user_app = models.ForeignKey(UserApp, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'user_app'), name='unique_user_app_added_by_user')
        ]


class UserAppPurchase(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='app_purchases')
    app = models.ForeignKey(UserApp, on_delete=models.CASCADE, related_name='purchases')
    transaction = models.OneToOneField('transactions.Transaction', on_delete=models.SET_NULL,
                                       related_name='user_app_purchase', null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.user} - {self.app} - {"PAID" if self.is_paid else "UNPAID"}'


class PlatformCommission(TimestampModel):
    commission_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('20.00'))


class UserAppBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_app_referral_balance")
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=255, default="USD")

    def __str__(self):
        return f"{self.user.username} - {self.current_balance} USDT"


class UserAppTransaction(TimestampModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="app_sales_profits")
    user_app_purchase = models.ForeignKey(UserAppPurchase, on_delete=models.CASCADE, related_name="referral_transactions")
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default="USD",
                                 related_name='user_app_sale_transactions')
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)
    profit_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.owner} +{self.profit_amount} {self.currency.code}"