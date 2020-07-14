from django.contrib.gis.db.models import PointField
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from common.models import TimestampModel, Currency, Country
from users.models import User


class OrganizationCategory(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Organization categories'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}'


class OrganizationType(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(OrganizationCategory, on_delete=models.CASCADE, related_name='types')

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return f'{self.title}'


class Organization(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_organizations')

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='organizations', default='KGS')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, related_name='countries', default='KG')
    image = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)
    show_contacts = models.BooleanField(default=False)
    types = models.ManyToManyField(OrganizationType, blank=True, related_name='organizations')
    address = models.CharField(max_length=255, null=True, blank=True)
    location = PointField(help_text="Для создания местоположения", null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return f'{self.title}'

    @property
    def full_location(self):
        full_location = dict(
            latitude=None if not self.location or not self.location.y else self.location.y,
            longitude=None if not self.location or not self.location.x else self.location.x
        )
        return full_location


class PhoneNumber(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='phone_numbers')
    phone_number = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.phone_number}'


class SocialNetworkContact(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='social_contacts')
    url = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.url}'


class Role(models.Model):
    title = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='roles')
    can_sale = models.BooleanField(default=False)
    can_check_attendance = models.BooleanField(default=False)
    can_see_stats = models.BooleanField(default=False)
    can_edit_organization = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.title} in {self.organization.title}'


class Membership(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='memberships')
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name='memberships')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='added_memberships')

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f'{self.user} as {self.role} in {self.organization}'


class DiscountCard(TimestampModel):
    FIXED = 'fixed'
    CUMULATIVE = 'cumulative'
    TYPES = (
        (FIXED, FIXED),
        (CUMULATIVE, CUMULATIVE),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='discounts')
    type = models.CharField(max_length=20, choices=TYPES, default=FIXED)
    percent = models.PositiveSmallIntegerField()
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='discounts', null=True, blank=True)
    limit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ('organization', 'type', 'percent', 'limit')

    def __str__(self):
        return f'{self.percent}% {self.type} card in {self.organization.title}'

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude)
        errors = {}

        if self.type == self.CUMULATIVE:
            if not self.currency:
                errors['currency'] = _('This field is required')
            if not self.limit:
                errors['limit'] = _('This field is required')

        if errors:
            raise ValidationError(errors)


class CardOwnership(TimestampModel):
    card = models.ForeignKey(DiscountCard, on_delete=models.PROTECT, related_name='owners')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cards')

    def __str__(self):
        return f'{self.card.type} card of {self.user} in {self.card.organization.title}'


class Subscription(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='subscriptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f'{self.user} subscribed to {self.organization}'
