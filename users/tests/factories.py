import factory
from rest_framework.authtoken.models import Token

from users.models import User, TemporaryPhoneNumber, TemporaryCode


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    phone_number = factory.Sequence(lambda n: f'996777000{n}')


class TokenFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Token

    user = factory.SubFactory(UserFactory)


class TemporaryPhoneNumberFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TemporaryPhoneNumber

    user = factory.SubFactory(UserFactory)


class TemporaryCodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TemporaryCode

    user = factory.SubFactory(UserFactory)
