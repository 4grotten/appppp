import factory

from common.models import Currency
from common.tests.factories import FileFactory
from organizations.models import (
    Organization, DiscountCard, OrganizationClientFinancialStatus, Partnership,
    CashbackGroup, Membership, Role, PhoneNumber
)
from users.tests.factories import UserFactory


def get_currency_usd():
    return Currency.objects.get(code="USD")


class CashbackGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CashbackGroup


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    owner = factory.SubFactory(UserFactory)
    cashback_group = factory.SubFactory(CashbackGroupFactory)
    title = factory.Sequence(lambda n: f'Organization {n}')
    currency = factory.LazyFunction(get_currency_usd)
    image = factory.SubFactory(FileFactory)


class PartnershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Partnership

    requested_by = factory.SubFactory(UserFactory)
    accepted_by = factory.SubFactory(UserFactory)


class DiscountCardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DiscountCard

    organization = factory.SubFactory(OrganizationFactory)
    percent = 0
    image = factory.SubFactory(FileFactory)


class OrganizationClientFinancialStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganizationClientFinancialStatus

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    card = factory.SubFactory(DiscountCardFactory)


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    organization = factory.SubFactory(OrganizationFactory)
    title = factory.Sequence(lambda n: f'Role{n}')


class MembershipFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Membership

    organization = factory.SubFactory(OrganizationFactory)
    user = factory.SubFactory(UserFactory)
    role = factory.SubFactory(RoleFactory)


class OrganizationPhoneNumberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PhoneNumber

    organization = factory.SubFactory(OrganizationFactory)


