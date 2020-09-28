from modeltranslation.decorators import register
from modeltranslation.translator import TranslationOptions

from .models import OrganizationCategory, OrganizationType


@register(OrganizationCategory)
class CategoryOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(OrganizationType)
class OrganizationOptions(TranslationOptions):
    fields = (
        'title',
    )
