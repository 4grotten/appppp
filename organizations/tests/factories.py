import factory

from organizations.models import (
    Organization, DiscountCard, OrganizationClientFinancialStatus, Partnership, CashbackGroup
)
from users.tests.factories import UserFactory


class CashbackGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CashbackGroup


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    owner = factory.SubFactory(UserFactory)
    cashback_group = factory.SubFactory(CashbackGroupFactory)
    title = factory.Sequence(lambda n: f'Organization {n}')


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


class OrganizationClientFinancialStatusFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrganizationClientFinancialStatus

    user = factory.SubFactory(UserFactory)
    organization = factory.SubFactory(OrganizationFactory)
    card = factory.SubFactory(DiscountCardFactory)
