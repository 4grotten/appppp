import factory

from common.tests.factories import CurrencyFactory
from organizations.tests.factories import OrganizationFactory, DiscountCardFactory
from transactions.models import Transaction
from users.tests.factories import UserFactory


class TransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Transaction

    client = factory.SubFactory(UserFactory)
    processed_by = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    currency = factory.SubFactory(CurrencyFactory)
    source_card = factory.SubFactory(DiscountCardFactory)
