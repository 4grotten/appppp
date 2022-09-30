import binascii
import datetime
import os
from decouple import config

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from common.models import TimestampModel
from common.utils import generate_random_code
from .constants import GENDER_CHOICES
from .managers import UserManager


class User(AbstractUser, TimestampModel):
    first_name = models.CharField(max_length=255, verbose_name='First Name', null=True, blank=True)
    last_name = models.CharField(max_length=255, verbose_name='Last Name', null=True, blank=True)
    full_name = models.CharField(max_length=255, verbose_name='Full Name', null=True, blank=True)
    email = models.EmailField(verbose_name='Email', blank=True, null=True)
    phone_number = PhoneNumberField(unique=True, max_length=255)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
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
        self.expired_time = datetime.datetime.now() + datetime.timedelta(days=int(self.expired_time_choice), minutes=0)
        return super(MyOwnToken, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key
