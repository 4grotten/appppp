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

    @classmethod
    def init_profile(cls, user: User, avatar_id: int, full_name: str, username: str,
                     date_of_birth, email: str, gender: str):

        try:
            user.avatar_id = avatar_id
            user.full_name = full_name
            user.username = username
            user.date_of_birth = date_of_birth
            user.email = email
            user.gender = gender

            user.save()

            return user

        except Exception as e:
            raise IntegrityException('Error while initializing profile')

    @classmethod
    def set_password(cls, user: User, password: str):

        if not user.is_new_user:
            raise ValidationException('Permission denied, you already set password')

        user.set_password(password)
        user.is_new_user = False
        user.save()


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
        try:
            temporary_code = cls.model.objects.get(code=code, user__phone_number=phone_number, is_used=False)

            if temporary_code.expiration_datetime < timezone.now():
                raise ValidationException('Code expired')

            cls.model.objects.filter(user__phone_number=phone_number).update(is_used=True)

        except cls.model.DoesNotExist:
            raise ValidationException('Code not found')
