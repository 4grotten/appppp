from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.utils import timezone

from common.exceptions import ObjectNotFoundException, IntegrityException, ValidationException
from users.models import TemporaryCode

User = get_user_model()


class UserService:
    model = User

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException('User not found')

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def create(cls, phone_number: str):
        try:
            return cls.model.objects.create(phone_number=phone_number)
        except IntegrityError:
            raise IntegrityException('Error while creating user')


class TemporaryCodeService:
    model = TemporaryCode

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException('Code not found')

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def create(cls, user: User):
        try:
            return cls.model.objects.create(user=user)
        except IntegrityError:
            raise IntegrityException('Error while creating temporary code')

    @classmethod
    def validate(cls, code: str, phone_number: str):
        temporary_codes = cls.filter(code=code, user__phone_number=phone_number)
        temporary_code = temporary_codes.last()

        print(temporary_code)

        if not temporary_codes or temporary_code.expiration_datetime < timezone.now():
            raise ValidationException('Invalid code')

        cls.filter(user__phone_number=phone_number).delete()
