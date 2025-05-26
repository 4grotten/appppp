import binascii
import datetime
import os
import random
import string
from decimal import Decimal

from decouple import config
from django.contrib.gis.db.models import PointField
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from common.models import TimestampModel, Currency
from common.utils import generate_random_code
from .constants import GENDER_CHOICES
from .managers import UserManager


class User(AbstractUser, TimestampModel):
    first_name = models.CharField(max_length=255, verbose_name='First Name', null=True, blank=True)
    last_name = models.CharField(max_length=255, verbose_name='Last Name', null=True, blank=True)
    full_name = models.CharField(max_length=255, verbose_name='Full Name', null=True, blank=True)
    email = models.EmailField(verbose_name='Email', blank=True, null=True)
    phone_number = PhoneNumberField(unique=True, max_length=255)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    avatar = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)
    is_new_user = models.BooleanField(default=True)
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    is_common_client = models.BooleanField(default=False, editable=False)

    objects = UserManager()

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return str(self.phone_number)

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        errors = {}
        if self.is_common_client:
            common_users = User.objects.filter(is_common_client=True)
            if common_users.count() > 0:
                if not common_users.first().id == self.id:
                    errors['is_common_client'] = _('Only one common client can exist')
        if errors:
            raise ValidationError(errors)

    # def save(self, *args, **kwargs):
    #     if not self.pk:
    #         self.email = "{}@example.com".format(uuid.uuid4().hex[:6].upper())
    #     super(User, self).save(*args, **kwargs)


class TemporaryCode(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.IntegerField(blank=True)
    is_used = models.BooleanField(default=False)
    expiration_datetime = models.DateTimeField(blank=True)

    def __str__(self):
        return str(self.user.phone_number)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.code = generate_random_code()
            self.expiration_datetime = datetime.datetime.now() + datetime.timedelta(minutes=2)
        super(TemporaryCode, self).save(*args, **kwargs)


class TemporaryPhoneNumber(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=255)
    code = models.IntegerField(blank=True)
    expiration_datetime = models.DateTimeField(blank=True)

    def __str__(self):
        return self.user.phone_number

    def save(self, *args, **kwargs):
        if not self.pk:
            self.code = generate_random_code()
            self.expiration_datetime = datetime.datetime.now() + datetime.timedelta(minutes=2)
        super(TemporaryPhoneNumber, self).save(*args, **kwargs)


class PhoneNumber(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_numbers')
    phone_number = models.CharField(max_length=255)

    def __str__(self):
        return self.phone_number


class SocialNetworkContact(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_contacts')
    url = models.CharField(max_length=255)

    def __str__(self):
        return self.url


class DeliveryAddress(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_addresses')
    address = models.CharField(max_length=225)
    apartment = models.CharField(max_length=36, null=True, blank=True)
    intercom = models.CharField(max_length=36, null=True, blank=True)
    entrance = models.CharField(max_length=36, null=True, blank=True)
    floor = models.CharField(max_length=36, null=True, blank=True)
    phone = models.CharField(max_length=36)
    comment = models.CharField(max_length=150, null=True, blank=True)
    location = PointField(help_text=_("Delivery location coordinates"), null=True, blank=True)
    by_default = models.BooleanField(default=False)


    def __str__(self):
        return self.address

    @property
    def full_location(self):
        if self.location and self.location.y and self.location.x:
            return dict(
                latitude=self.location.y,
                longitude=self.location.x
            )
        return None


class MyOwnToken(TimestampModel):
    """
    The default authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40)
    user = models.ForeignKey(User, related_name='auth_tokens', on_delete=models.CASCADE, verbose_name="User")
    ip = models.CharField(max_length=256, null=True, blank=True)
    location = models.CharField(max_length=256, null=True, blank=True)
    device = models.CharField(max_length=256, null=True, blank=True)
    expired_time = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    log_time = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(default=timezone.now)
    version_app = models.CharField(max_length=500, null=True, blank=True)
    operating_system = models.CharField(max_length=500, null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    expired_time_choice = models.PositiveIntegerField(default=30)

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        self.expired_time = timezone.now() + datetime.timedelta(days=int(self.expired_time_choice), minutes=0)
        return super(MyOwnToken, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key


class PromoCode(TimestampModel):
    owner = models.OneToOneField('User', on_delete=models.CASCADE, related_name='promo_code')
    code = models.CharField(max_length=255, unique=True)
    discount_percent = models.DecimalField(default=10.0, max_digits=5, decimal_places=2)
    profit_percent = models.DecimalField(default=10.0, max_digits=5, decimal_places=2)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        charset = string.ascii_uppercase + string.digits
        while True:
            prefix = ''.join(random.choices(charset, k=12))
            new_code = f"{prefix}{self.owner.id}"
            if not PromoCode.objects.filter(code=new_code).exists():
                return new_code


class ReferralTransaction(TimestampModel):
    promocode = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name="referral_transactions")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referral_profits")
    referred_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="used_promocodes")
    subscription = models.ForeignKey("organizations.UserOrgSubscription", on_delete=models.CASCADE)
    profit_amount_usdt = models.DecimalField(max_digits=10, decimal_places=2)
    original_currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='referral_transactions',
                                          default='USD')
    original_amount = models.DecimalField(max_digits=10, decimal_places=2)


class ReferralBalance(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="referral_balance")
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=255, default="USDT")

    def __str__(self):
        return f"{self.user.username} - {self.current_balance} USDT"


class ReferralWithdrawal(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="referral_withdrawals")
    amount_usdt = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("completed", "Completed")])
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount_usdt} USDT ({self.status})"
