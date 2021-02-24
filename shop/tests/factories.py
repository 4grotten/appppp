import factory

from organizations.tests.factories import OrganizationFactory
from shop.models import ShopItem, Cart, CartItem
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory


class ShopItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShopItem

    organization = factory.SubFactory(OrganizationFactory)
    name = factory.Sequence(lambda n: f'Shop item{n}')


class CartFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Cart

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)


class CartItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CartItem

    cart = factory.SubFactory(CartFactory)
    item = factory.SubFactory(ShopItemFactory)
    count = factory.Sequence(lambda n: int(n + 5))
