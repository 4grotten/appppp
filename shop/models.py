from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from common.models import TimestampModel, File
from organizations.models import Organization


class MainCategory(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name_plural = 'Main categories'


class ItemCategory(models.Model):
    main_category = models.ForeignKey(MainCategory, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=64)

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='item_categories')

    def __str__(self):
        return f'{self.name}'

    class Meta:
        verbose_name_plural = 'Item categories'
        ordering = ('-organization', 'name',)


class ShopItem(TimestampModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='shop_items')
    category = models.ForeignKey(ItemCategory, on_delete=models.CASCADE, related_name='items_in_category')

    name = models.CharField(max_length=64)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.PositiveSmallIntegerField(null=True, blank=True,
                                                validators=[MinValueValidator(0), MaxValueValidator(100)])
    article = models.CharField(max_length=64, null=True, blank=True)
    instagram_link = models.URLField(null=True, blank=True)
    images = models.ManyToManyField(File, blank=True, related_name='shop_items')

    def __str__(self):
        return f'{self.name}'


class YoutubeLink(models.Model):
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE, related_name='youtube_links')
    link = models.URLField(null=True, blank=True)

    def __str__(self):
        return f'YT link #{self.id} for {self.item.name}'
