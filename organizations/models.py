from django.db import models

from common.models import TimestampModel
from users.models import User


class OrganizationCategory(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = 'Organization categories'

    def __str__(self):
        return f'{self.name}'


class OrganizationType(models.Model):
    title = models.CharField(max_length=255)
    category = models.ForeignKey(OrganizationCategory, on_delete=models.CASCADE, related_name='types')

    def __str__(self):
        return f'{self.title}'


class Organization(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_organizations')

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    opens_at = models.TimeField(null=True, blank=True)
    closes_at = models.TimeField(null=True, blank=True)
    types = models.ManyToManyField(OrganizationType, blank=True, related_name='organizations')
    image = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, blank=True)
    show_contacts = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.title}'


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
