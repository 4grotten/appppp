from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

from common.models import TimestampModel, File
from organizations.models import Organization
from transactions.models import Transaction
from users.models import User


class ItemCategory(models.Model):
    name = models.CharField(max_length=64)
    icon = models.OneToOneField(File, on_delete=models.SET_NULL, null=True, blank=True)
    is_adult = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name_plural = 'Item categories'


class ItemSubcategory(models.Model):
    category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=64)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='item_categories')

    def __str__(self):
        return f'{self.name}: {self.category.name}'

    class Meta:
        verbose_name_plural = 'Item subcategories'
        ordering = ('-organization', 'name',)


class ShopItem(models.Model):
    updated_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='shop_items')
    subcategory = models.ForeignKey(ItemSubcategory, on_delete=models.CASCADE, related_name='items_in_category',
                                    null=True, blank=True)
    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.PositiveSmallIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    article = models.CharField(max_length=64, null=True, blank=True)
    instagram_link = models.URLField(null=True, blank=True)
    images = models.ManyToManyField(File, blank=True, related_name='shop_items')
    youtube_links = models.JSONField(null=True)
    is_updated = models.BooleanField(default=False)

    is_published = models.BooleanField(default=True)
    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name}'

    def save(self, *args, **kwargs):
        if self.id:
            self.updated_at = timezone.now()
            self.is_updated = True
        if self.price is not None:
            self.discounted_price = self.price * (100 - self.discount) / 100
        if self.subcategory is not None and self.subcategory.category.is_adult:
            self.is_hidden = True
        else:
            self.is_hidden = False
        super().save(*args, **kwargs)


class ItemInstagramData(TimestampModel):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='instagram_data')
    thumbnail_url = models.URLField(max_length=5000)
    video_url = models.URLField(max_length=5000, null=True, blank=True)

    def __str__(self):
        return f'Data for {self.item}'


class ItemLike(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='liked_items')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='liked_users')

    def __str__(self):
        return f'{self.user} liked {self.item.name}'

    class Meta:
        constraints = (
            models.constraints.UniqueConstraint(fields=('user', 'item'), name='unique_user_item_like'),
        )


class ItemBookmark(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarked_items')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='bookmarked_users')

    def __str__(self):
        return f'{self.user} bookmarked {self.item.name}'

    class Meta:
        constraints = (
            models.constraints.UniqueConstraint(fields=('user', 'item'), name='unique_user_item_bookmark'),
        )


class Cart(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='carts')
    is_open = models.BooleanField(default=True)
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, related_name='cart', null=True)

    def __str__(self):
        return f'Cart of {self.user} in {self.organization}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('organization', 'user'), condition=Q(is_open=True),
                                    name='unique_cart_for_user_in_organization')
        ]


class CartItem(TimestampModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='user_carts')
    count = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'Item #{self.item.id} in cart of {self.cart.user}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('cart', 'item'), name='unique_item_in_user_cart')
        ]
        ordering = ['-created_at']


class DeliveryInfo(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_infos')
    transaction = models.OneToOneField(Transaction, on_delete=models.SET_NULL, null=True, related_name='delivery_info')
    address = models.CharField(max_length=225)
    apartment = models.CharField(max_length=36, null=True, blank=True)
    intercom = models.CharField(max_length=36, null=True, blank=True)
    entrance = models.CharField(max_length=36, null=True, blank=True)
    floor = models.CharField(max_length=36, null=True, blank=True)
    phone = models.CharField(max_length=36)
    comment = models.CharField(max_length=150, null=True, blank=True)

    def __str__(self):
        return f'Delivery info of {self.user}'


class Complaint(TimestampModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints')
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='complaints')
    reason = models.TextField(max_length=800)

    def __str__(self):
        return f'Complaint of {self.user} about {self.item.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('user', 'item'), name='unique_complaint_from_user')
        ]
