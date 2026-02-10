"""Unmanaged models for EasyCard database integration.

These models mirror the EasyCard PostgreSQL schema.
They are read-only from the Apofiz perspective.
"""

from django.db import models


class EasyCardProfile(models.Model):
    """User profile from EasyCard database.

    Maps to: public.profiles table
    Synced from Apofiz User model.
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("moderator", "Moderator"),
        ("admin", "Admin"),
        ("root", "Root"),
    ]

    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField(unique=True)
    apofiz_user_id = models.BigIntegerField(
        unique=True,
        null=True,
        blank=True,
        help_text="User ID from Apofiz backend (primary link)",
    )
    phone = models.CharField(max_length=20, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    full_name = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    language = models.CharField(max_length=10, default="en")
    avatar_url = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")
    web_links = models.JSONField(default=list, blank=True)
    payment_links = models.JSONField(default=list, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    company_name = models.CharField(max_length=255, null=True, blank=True)
    company_logo = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "profiles"
        app_label = "easycard_integration"
        verbose_name = "EasyCard Profile"
        verbose_name_plural = "EasyCard Profiles"

    def __str__(self):
        name = self.full_name or f"{self.first_name or ''} {self.last_name or ''}".strip()
        return f"{name or 'Unknown'} ({self.phone or 'no phone'})"

    @property
    def display_name(self):
        """Return display name of the user."""
        if self.full_name:
            return self.full_name
        parts = [self.first_name, self.last_name]
        return " ".join(p for p in parts if p) or "Unknown"


class EasyCardCard(models.Model):
    """Card from EasyCard database.

    Maps to: public.cards table
    """

    CARD_TYPE_CHOICES = [
        ("virtual", "Virtual"),
        ("metal", "Metal"),
    ]

    CARD_STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("blocked", "Blocked"),
        ("expired", "Expired"),
    ]

    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField()
    type = models.CharField(max_length=10, choices=CARD_TYPE_CHOICES, default="virtual")
    name = models.CharField(max_length=255, default="My Card")
    status = models.CharField(
        max_length=10, choices=CARD_STATUS_CHOICES, default="inactive"
    )
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    last_four_digits = models.CharField(max_length=4, null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    annual_fee = models.DecimalField(max_digits=10, decimal_places=2, default=183.00)
    activated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "cards"
        app_label = "easycard_integration"
        verbose_name = "EasyCard Card"
        verbose_name_plural = "EasyCard Cards"

    def __str__(self):
        return f"{self.name} (*{self.last_four_digits or '****'}) - {self.balance} AED"


class EasyCardTransaction(models.Model):
    """Transaction from EasyCard database.

    Maps to: public.transactions table
    """

    TRANSACTION_TYPE_CHOICES = [
        ("top_up", "Top Up"),
        ("withdrawal", "Withdrawal"),
        ("transfer_in", "Transfer In"),
        ("transfer_out", "Transfer Out"),
        ("card_payment", "Card Payment"),
        ("refund", "Refund"),
        ("fee", "Fee"),
        ("cashback", "Cashback"),
        ("card_activation", "Card Activation"),
    ]

    TRANSACTION_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField()
    card_id = models.UUIDField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(
        max_length=20, choices=TRANSACTION_STATUS_CHOICES, default="pending"
    )
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    currency = models.CharField(max_length=3, default="AED")
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exchange_rate = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    original_amount = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True
    )
    original_currency = models.CharField(max_length=3, null=True, blank=True)
    merchant_name = models.TextField(null=True, blank=True)
    merchant_category = models.TextField(null=True, blank=True)
    recipient_card = models.CharField(max_length=19, null=True, blank=True)
    sender_name = models.TextField(null=True, blank=True)
    sender_card = models.CharField(max_length=19, null=True, blank=True)
    reference_id = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "transactions"
        app_label = "easycard_integration"
        verbose_name = "EasyCard Transaction"
        verbose_name_plural = "EasyCard Transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type}: {self.amount} {self.currency} ({self.status})"


class EasyCardUserRole(models.Model):
    """User role from EasyCard database.

    Maps to: public.user_roles table
    """

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("moderator", "Moderator"),
        ("user", "User"),
    ]

    id = models.UUIDField(primary_key=True)
    user_id = models.UUIDField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "user_roles"
        app_label = "easycard_integration"
        verbose_name = "EasyCard User Role"
        verbose_name_plural = "EasyCard User Roles"
        unique_together = [["user_id", "role"]]

    def __str__(self):
        return f"User {self.user_id}: {self.role}"


class EasyCardAdminSettings(models.Model):
    """Admin settings from EasyCard database.

    Maps to: public.admin_settings table
    Categories: 'exchange_rates', 'fees', 'limits'
    """

    id = models.UUIDField(primary_key=True)
    category = models.CharField(max_length=50)
    key = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=15, decimal_places=6)
    description = models.TextField(null=True, blank=True)
    updated_by = models.UUIDField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "admin_settings"
        app_label = "easycard_integration"
        verbose_name = "EasyCard Admin Setting"
        verbose_name_plural = "EasyCard Admin Settings"
        unique_together = [["category", "key"]]

    def __str__(self):
        return f"{self.category}.{self.key} = {self.value}"
