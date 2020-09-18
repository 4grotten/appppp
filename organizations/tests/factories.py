import factory

from organizations.models import Organization, DiscountCard, OrganizationClientFinancialStatus, Partnership
from users.tests.factories import UserFactory


class OrganizationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Organization

    owner = factory.SubFactory(UserFactory)


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
