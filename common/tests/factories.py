import factory
from django.core.files.base import ContentFile

from common.models import Currency, File


class CurrencyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Currency


class FileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = File

    file = factory.LazyAttribute(
            lambda _: ContentFile(
                factory.django.ImageField()._make_data(
                    {'width': 1024, 'height': 768}
                ), 'example.jpg'
            )
        )
