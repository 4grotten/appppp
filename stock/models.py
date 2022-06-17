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
