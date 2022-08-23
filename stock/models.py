from django.core import validators
from django.db import models

from common.models import File


class FormatCriteria(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'


class CriteriaSubcategory(models.Model):
    name = models.CharField(max_length=255)
    format_criteria = models.ManyToManyField(FormatCriteria, related_name='criteria_subcategories',
                                             blank=True)
    icon = models.OneToOneField(File, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Criterion of subcategory'
        verbose_name_plural = 'Criteria of subcategory'

    def __str__(self):
        return f'{self.name}'


class SizeFormat(models.Model):
    format_criteria = models.ForeignKey(FormatCriteria, on_delete=models.CASCADE, related_name='size_formats')
    size = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('format_criteria', 'order')

    def __str__(self):
        return f'Format - {self.format_criteria.name} size - {self.size}'


class ShopItemSetStock(models.Model):
    main_shop_item = models.ForeignKey('shop.ShopItem', on_delete=models.CASCADE,
                                       related_name='main_shop_items_set_stocks')
    shop_item = models.ManyToManyField('shop.ShopItem', related_name='shop_items_set_stocks', blank=True)

    def __str__(self):
        return f'Set stock of {self.main_shop_item}'


class ShopItemLinksSetStock(models.Model):
    main_shop_item = models.ForeignKey('shop.ShopItem', on_delete=models.CASCADE,
                                       related_name='main_item_link_set_stocks')
    shop_item = models.ForeignKey('shop.ShopItem', on_delete=models.CASCADE,
                                  related_name='shop_items_link_set_stocks', null=True, blank=True)
    link = models.URLField(null=True, blank=True, max_length=1000)

    def __str__(self):
        return f'Link {self.link}'


class ShopItemSizeCount(models.Model):
    main_shop_item = models.ForeignKey('shop.ShopItem', on_delete=models.CASCADE,
                                       related_name='shop_item_size_counts')
    size = models.ForeignKey(SizeFormat, on_delete=models.CASCADE, related_name='shop_item_size_counts', null=True,
                             blank=True)
    count = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('main_shop_item', 'size')

    def __str__(self):
        return f'size count of shop item - {self.main_shop_item}'
