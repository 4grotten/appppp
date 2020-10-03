from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from common.models import TimestampModel, File
from organizations.models import Organization


class ItemCategory(models.Model):
    name = models.CharField(max_length=64)

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
        return f'{self.name}'

    class Meta:
        verbose_name_plural = 'Item subcategories'
        ordering = ('-organization', 'name',)


class ShopItem(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='shop_items')
    subcategory = models.ForeignKey(ItemSubcategory, on_delete=models.CASCADE, related_name='items_in_category')

    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.PositiveSmallIntegerField(null=True, blank=True,
                                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    article = models.CharField(max_length=64, null=True, blank=True)
    instagram_link = models.URLField(null=True, blank=True)
    images = models.ManyToManyField(File, blank=True, related_name='shop_items')
    youtube_links = JSONField(null=True)

    is_published = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name}'
