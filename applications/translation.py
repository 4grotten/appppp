from modeltranslation.decorators import register
from modeltranslation.translator import TranslationOptions

from applications.models import UserAppCategory, UserAppType


@register(UserAppCategory)
class UserAppCategoryOptions(TranslationOptions):
    fields = (
        'name',
    )


@register(UserAppType)
class UserAppTypeOptions(TranslationOptions):
    fields = (
        'title',
    )
