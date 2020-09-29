from modeltranslation.translator import TranslationOptions
from modeltranslation.decorators import register

from .models import Notification


@register(Notification)
class NotificationOptions(TranslationOptions):
    fields = (
        'title', 'description'
    )
