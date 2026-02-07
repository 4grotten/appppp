import uuid

from django.db import models

from common.models import File, TimestampModel


class SavedContact(TimestampModel):
    """
    Saved contact model for EasyCard PWA.
    Stores user's saved contacts with payment methods and social links.
    """

    PAYMENT_TYPE_CHOICES = [
        ('card', 'Card'),
        ('iban', 'IBAN'),
        ('crypto', 'Crypto'),
        ('paypal', 'PayPal'),
        ('applepay', 'Apple Pay'),
        ('googlepay', 'Google Pay'),
        ('wallet', 'Wallet'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='saved_contacts',
        verbose_name='Owner'
    )
    full_name = models.CharField(max_length=255, verbose_name='Full Name')
    phone = models.CharField(max_length=50, blank=True, null=True, verbose_name='Phone')
    email = models.EmailField(blank=True, null=True, verbose_name='Email')
    company = models.CharField(max_length=255, blank=True, null=True, verbose_name='Company')
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name='Position')
    avatar = models.ForeignKey(
        File,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='saved_contact_avatars',
        verbose_name='Avatar'
    )
    notes = models.TextField(blank=True, null=True, verbose_name='Notes')
    payment_methods = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Payment Methods',
        help_text='Array of PaymentMethod objects: [{id, type, label, value, network?}]'
    )
    social_links = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Social Links',
        help_text='Array of ContactSocialLink objects: [{id, networkId, networkName, url}]'
    )

    class Meta:
        verbose_name = 'Saved Contact'
        verbose_name_plural = 'Saved Contacts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['full_name']),
        ]

    def __str__(self):
        return f"{self.full_name} ({self.user})"

    @property
    def avatar_url(self):
        """Return avatar URL if avatar exists."""
        if self.avatar and self.avatar.file:
            return self.avatar.file.url
        return None
