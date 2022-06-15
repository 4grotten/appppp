from django.db import models


class FormatSize(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.name}'


class ShopItemSize(models.Model):
    format_size = models.ForeignKey(FormatSize, on_delete=models.CASCADE, related_name='shop_item_sizes')
    size = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('format_size', 'order')

    def __str__(self):
        return f'Format - {self.format_size.name} size - {self.size}'
