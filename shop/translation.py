from modeltranslation.decorators import register
from modeltranslation.translator import TranslationOptions

from shop.models import MainCategory, ItemCategory


@register(MainCategory)
class MainCategoryOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(ItemCategory)
class ItemCategoryOptions(TranslationOptions):
    fields = (
        'name',
    )
