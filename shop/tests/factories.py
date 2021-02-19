import factory
from shop.models import ShopItem


class ShopItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShopItem
