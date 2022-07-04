from django.db import models


class FormatCriteria(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'


class CriteriaSubcategory(models.Model):
    name = models.CharField(max_length=255)
    format_criteria = models.ManyToManyField(FormatCriteria, related_name='criteria_subcategories',
                                             blank=True)

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


class StockCart(models.Model):
    shop_item = models.ForeignKey("shop.ShopItem", related_name='stock_carts', on_delete=models.CASCADE,
                                  blank=True)
    available_size = models.ManyToManyField(SizeFormat, related_name='stock_carts')

    class Meta:
        verbose_name = 'Shop item stock cart'
        verbose_name_plural = 'Shop item stock carts'

    def __str__(self):
        return f'Shop item: {self.shop_item} - {self.available_size}'


class ShopItemSizeCount(models.Model):
    size_format = models.ForeignKey(SizeFormat, related_name='shop_item_size_counts', on_delete=models.CASCADE,
                                    blank=True)
    stock_cart = models.ForeignKey(StockCart, related_name='shop_item_size_counts', on_delete=models.CASCADE,
                                   blank=True)
    quantity = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Shop item size quantity'
        verbose_name_plural = 'Shop item sizes quantity'

    def __str__(self):
        return f'{self.size_format} - {self.quantity}'


class ShopItemLinkForCollection(models.Model):
    link = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'Shop item link for collection'
        verbose_name_plural = 'Shop item links for collection'

    def __str__(self):
        return f'{self.id}'


class ShopItemCollections(models.Model):
    main_item = models.ForeignKey("shop.ShopItem", related_name='shop_collections', on_delete=models.CASCADE,
                                  blank=True)
    related_items = models.ManyToManyField("shop.ShopItem", related_name='shop_item_collections', blank=True)
    related_item_links = models.ManyToManyField(ShopItemLinkForCollection, related_name='shop_item_link_collections', blank=True)

    class Meta:
        verbose_name = 'Shop item collection'
        verbose_name_plural = 'Shop item collections'

    def __str__(self):
        return f'{self.id} - {self.main_item}'
