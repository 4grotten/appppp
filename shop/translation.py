from modeltranslation.decorators import register
from modeltranslation.translator import TranslationOptions

from shop.models import ItemCategory, ItemSubcategory


@register(ItemCategory)
class ItemCategoryOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(ItemSubcategory)
class ItemSubcategoryOptions(TranslationOptions):
    fields = (
        'name',
    )
