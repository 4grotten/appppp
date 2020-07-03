from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils import timezone

from common.exceptions import ObjectNotFoundException, IntegrityException, ValidationException
from sms_sender.services import MessageService
from .constants import SMS_CODE_MESSAGE
from .models import TemporaryCode, PhoneNumber, SocialNetworkContact, TemporaryPhoneNumber

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
    def create(cls, phone_number: str) -> User:
        try:
            return cls.model.objects.create(phone_number=phone_number)
        except IntegrityError:
            raise IntegrityException('Error while creating user')

    @classmethod
    def init_profile(cls, user: User, avatar_id: int, full_name: str, username: str,
                     date_of_birth, gender: str):

        try:
            user.avatar_id = avatar_id
            user.full_name = full_name
            user.username = username
            user.date_of_birth = date_of_birth
            user.gender = gender
            user.is_new_user = False

            user.save()

            return user

        except Exception as e:
            raise IntegrityException('Error while initializing profile')

    @classmethod
    def set_password(cls, user: User, password: str):
        user.set_password(password)
        user.is_new_user = False
        user.save()

    @classmethod
    def change_password(cls, user: User, new_password: str, old_password: str):
        if not user.check_password(old_password):
            raise ValidationException('Incorrect old password')

        user.set_password(new_password)
        user.save()

    @classmethod
    def change_phone_number(cls, user: User, new_phone_number: str):
        try:
            user.phone_number = new_phone_number
            user.save()
        except Exception:
            raise IntegrityException('Error while changing number')

    @staticmethod
    def is_email_updated(user, email):
        return user == email

    @classmethod
    def init_or_update_user_email(cls, user, email):
        if not cls.is_email_updated(user=user, email=email):
            user.email = email
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
    def create_and_send(cls, user: User) -> TemporaryCode:
        try:

            current_datetime = timezone.now()
            max_datetime = current_datetime + timezone.timedelta(seconds=-10)

            if cls.model.objects.filter(user=user,
                                        created_at__range=(max_datetime, current_datetime)).count() >= 2:
                raise ValidationException('Limit exceeded')

            code = cls.model.objects.create(user=user)
        except IntegrityError:
            raise IntegrityException('Error while creating temporary code')

        message = SMS_CODE_MESSAGE.format(code.code)
        sms_id = f'{user.id}{code.code}'
        MessageService.send_sms(numbers=[user.phone_number], message=message, sms_id=sms_id)
        return code

    @classmethod
    def validate(cls, code: str, phone_number: str):
        try:
            temporary_code = cls.model.objects.get(code=code, user__phone_number=phone_number, is_used=False)

            if temporary_code.expiration_datetime < timezone.now():
                raise ValidationException('Code expired')

            cls.model.objects.filter(user__phone_number=phone_number).update(is_used=True)

        except cls.model.DoesNotExist:
            raise ValidationException('Code not found')


class PhoneNumberService:
    model = PhoneNumber

    @classmethod
    def get_numbers_of_user(cls, user_id: int) -> QuerySet:
        return PhoneNumber.objects.filter(user_id=user_id)

    @classmethod
    def update_phone_numbers(cls, user: User, numbers: list):
        with transaction.atomic():
            PhoneNumber.objects.filter(user=user).delete()
            numbers = [PhoneNumber(user=user, phone_number=number) for number in numbers]
            PhoneNumber.objects.bulk_create(numbers)
            return numbers


class SocialNetworkContactService:
    model = SocialNetworkContact

    @classmethod
    def get_networks_of_user(cls, user_id: int) -> QuerySet:
        return SocialNetworkContact.objects.filter(user_id=user_id)

    @classmethod
    def update_social_networks(cls, user: User, urls: list):
        with transaction.atomic():
            SocialNetworkContact.objects.filter(user=user).delete()
            contacts = [SocialNetworkContact(user=user, url=url) for url in urls]
            SocialNetworkContact.objects.bulk_create(contacts)
            return contacts


class TemporaryPhoneNumberService:
    model = TemporaryPhoneNumber

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException('Temporary phone number not found')

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def create(cls, user: User, phone_number: str):
        try:

            current_datetime = timezone.now()
            max_datetime = current_datetime + timezone.timedelta(seconds=-10)

            if cls.model.objects.filter(user=user,
                                        created_at__range=(max_datetime, current_datetime)).count() >= 2:
                raise ValidationException('Limit exceeded')

            code = cls.model.objects.create(user=user, phone_number=phone_number)

            message = SMS_CODE_MESSAGE.format(code.code)
            sms_id = f'{user.id}{code.code}'
            MessageService.send_sms(numbers=[phone_number], message=message, sms_id=sms_id)

        except IntegrityError:
            raise IntegrityException('Error while creating temporary code for new phone_number')

    @classmethod
    def validate(cls, code: str, phone_number: str):
        try:
            temporary_code = cls.model.objects.get(code=code, user__phone_number=phone_number)

            if temporary_code.expiration_datetime < timezone.now():
                raise ValidationException('Code expired')

            cls.model.objects.filter(user__phone_number=phone_number).delete()

        except cls.model.DoesNotExist:
            raise ValidationException('Code not found')
