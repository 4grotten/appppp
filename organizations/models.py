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
    can_send_message = models.BooleanField(default=True)
    can_edit_partner = models.BooleanField(default=False)

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

    next_cumulative = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True,
                                           related_name='previous_cumulative')

    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ('organization', 'type', 'limit', 'percent',)
        constraints = [
            models.UniqueConstraint(fields=('organization', 'type', 'percent'), name='unique_percents_of_organization'),
            models.UniqueConstraint(fields=('organization', 'type', 'limit'), name='unique_limits_of_organization'),
        ]

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


class CardBackground(models.Model):
    image = models.ForeignKey('common.File', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='backgrounds')

    def __str__(self):
        return f'Card background #{self.id}: {self.image}'


class OrganizationClientFinancialStatus(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='cards')
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, related_name='client_statuses')
    card = models.ForeignKey(DiscountCard, on_delete=models.PROTECT, related_name='clients', null=True, blank=True)
    total_spent = models.DecimalField(max_digits=16, decimal_places=2, default=0, editable=False)
    total_saved = models.DecimalField(max_digits=16, decimal_places=2, default=0, editable=False)

    def __str__(self):
        return f'{self.user} in {self.organization.title} has spent {self.total_spent} {self.organization.currency}'

    class Meta:
        verbose_name_plural = 'Organization client financial statuses'
        constraints = [
            models.UniqueConstraint(fields=('user', 'organization'), name='unique_statuses_of_user_in_organization')
        ]


class Subscription(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='subscriptions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f'{self.user} subscribed to {self.organization}'


class Partnership(TimestampModel):
    requested_by = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='requested_partnerships')
    accepted_by = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='accepted_partnerships')

    is_accepted = models.BooleanField(default=False)

    can_check_attendance = models.BooleanField(default=False)
    can_see_stats = models.BooleanField(default=False)
    can_edit_organization = models.BooleanField(default=False)

    class Meta:
        constraints = (
            models.UniqueConstraint(fields=('requested_by', 'accepted_by'), name='unique_partnerships'),
        )

    def __str__(self):
        return f'{self.accepted_by} accepted partnership of {self.requested_by}'


class Banner(TimestampModel):
    host_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='hosted_banners',
                                          null=True, blank=True)
    linked_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='leading_banners')

    image = models.ForeignKey('common.File', on_delete=models.CASCADE, related_name='banners')

    def __str__(self):
        return f'Banner of {self.linked_organization} hosted by {self.host_organization}'


class Message(TimestampModel):
    sender = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sender')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='sender_organization')
    content = models.CharField(blank=False, null=False, max_length=800)

    def __str__(self):
        return f'Message of {self.organization.title}'
