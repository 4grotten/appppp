from typing import Union

from django.contrib.gis.geos import Point
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException, IntegrityException, ValidationException, BadRequestException
from common.services import slack
from mailer.services import MailerService
from sms_sender.services import MessageServiceNIKITA, MessageServiceTwilio, AzamatMessageService, \
    MessageServiceMessageBird
from .constants import SMS_CODE_MESSAGE
from .models import TemporaryCode, PhoneNumber, SocialNetworkContact, TemporaryPhoneNumber, MyOwnToken, DeliveryAddress
from user_agents import parse

User = get_user_model()


class UserService:
    model = User

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('User not found'))

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def create(cls, phone_number: str) -> User:
        try:
            return cls.model.objects.create(phone_number=phone_number)
        except IntegrityError:
            raise IntegrityException(_('Error while creating user'))

    @classmethod
    def init_profile(cls, user: User, avatar_id: int, full_name: str, username: str,
                     date_of_birth, gender: Union[str, None], email: Union[str, None]):

        try:
            user.avatar_id = avatar_id
            user.full_name = full_name
            user.username = username
            user.date_of_birth = date_of_birth
            user.gender = gender
            user.is_new_user = False
            user.email = email
            user.save()

            return user

        except Exception as e:
            raise IntegrityException(_('Error while initializing profile'))

    @classmethod
    def set_password(cls, user: User, password: str):
        user.set_password(password)
        user.is_new_user = False
        user.save(update_fields=["password", "is_new_user"])

    @classmethod
    def change_password(cls, user: User, new_password: str, old_password: str):
        if not user.check_password(old_password):
            raise ValidationException(_('Incorrect old password'))

        user.set_password(new_password)
        user.save(update_fields=["password"])

    @classmethod
    def change_phone_number(cls, user: User, new_phone_number: str):
        try:
            user.phone_number = new_phone_number
            user.save(update_fields=["phone_number"])
        except Exception:
            raise IntegrityException(_('Error while changing number'))

    @classmethod
    def get_common_user(cls) -> User:
        return cls.get(is_common_client=True)

    @classmethod
    def get_user_email_by_phone_number(cls, phone_number: str):
        try:
            user = cls.model.objects.get(phone_number=phone_number)
            return user.email
        except User.DoesNotExist:
            return None

    @classmethod
    def get_data_with_valid_location(cls, request):
        location = request.data.get('location', None)
        if location == '':
            request.data['location'] = None
        return request.data

    @classmethod
    def get_location_info(cls, serializer):
        location = serializer.validated_data.get('location')
        if location is None:
            try:
                response_ip = get('https://api64.ipify.org?format=json').json()
                loc = get(f'https://ipapi.co/{response_ip["ip"]}/json/')
                locs = loc.json()
                locs = dict(locs)
                location = f"{locs['country_name']} {locs['city']}"
            except:
                location = 'Not found'
        return location


class MyOwnTokenService:
    model = MyOwnToken

    @classmethod
    def get_or_create_token(cls, user, request, location=None, device_info=None):
        try:
            if location and device_info:
                token = MyOwnToken.objects.get(user=user, device=device_info['device'],
                                               operating_system=device_info['operating_system'],
                                               version_app=device_info['version_app'], is_active=True,
                                               user_agent=device_info['us_agent'],
                                               ip=request.META.get('REMOTE_ADDR'))
            else:
                token = MyOwnToken.objects.get(user=user, is_active=True, ip=request.META.get('REMOTE_ADDR'))
        except MyOwnToken.DoesNotExist:
            if location and device_info:
                token = MyOwnToken.objects.create(user=user, location=location, device=device_info['device'],
                                              ip=request.META.get('REMOTE_ADDR'),
                                              operating_system=device_info['operating_system'],
                                              version_app=device_info['version_app'],
                                              user_agent=device_info['us_agent'])
            else:
                token = MyOwnToken.objects.create(user=user, ip=request.META.get('REMOTE_ADDR'))
            token.save()

        return token

    @classmethod
    def get_device_info(cls, serializer, request):
        data = dict()
        headers = request.headers['User-Agent']
        user_agent = parse(headers)
        data['device'] = serializer.validated_data.get('device')
        data['version_app'] = serializer.validated_data.get('version_app')
        data['operating_system'] = serializer.validated_data.get('operating_system')

        if data['operating_system'] == 'android':
            data['us_agent'] = f"{data['device']} {data['operating_system']}/ {data['version_app']} / {headers}"
        elif data['operating_system'] == 'ios':
            data['us_agent'] = f"{data['device']} {data['operating_system']}/ {data['version_app']} / {headers}"
        else:
            data['device'] = f'{user_agent.os.family} {user_agent.os.version_string}'
            data['us_agent'] = request.headers.get('User-Agent')
            data['version_app'] = f'Apofiz Web / {user_agent.browser.family} - {user_agent.browser.version}'

        return data

    @classmethod
    def save_device_info(cls, request, serializer):
        token_key = request.headers['Authorization'].split()[1]
        token = MyOwnToken.objects.get(key=token_key)
        location = UserService.get_location_info(serializer=serializer)
        device_info = cls.get_device_info(serializer=serializer, request=request)
        token.location = location
        token.device = device_info['device']
        token.version_app = device_info['version_app']
        token.operating_system = device_info['operating_system']
        token.user_agent = device_info['us_agent']
        token.save()






class TemporaryCodeService:
    model = TemporaryCode
    nurtelecom = (
        '+996500', '+996501', '+996502', '+996503', '+996504', '+996505', '+996506', '+996507', '+996508',
        '+996509', '+996700', '+996701', '+996702', '+996703', '+996704', '+996705', '+996706', '+996707',
        '+996708', '+996709'
    )

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Code not found'))

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def create_and_send(cls, user: User, whatsapp: bool = None, email: bool = None,
                        ip_addr: str = None) -> TemporaryCode:
        try:
            current_datetime = timezone.now()
            # max_datetime = current_datetime + timezone.timedelta(minutes=-30)

            # if cls.model.objects.filter(user=user,
            #                             created_at__range=(max_datetime, current_datetime)).count() >= 8:
            #     raise ValidationException(_('Limit exceeded'))

            code = cls.model.objects.create(user=user)
        except IntegrityError:
            raise IntegrityException(_('Error while creating temporary code'))

        message = SMS_CODE_MESSAGE.format(code.code)
        sms_id = f'{user.id}{code.code}'
        phone_number = str(user.phone_number)
        # if phone_number.startswith(cls.nurtelecom):
        if whatsapp == True:
            MessageServiceTwilio.send_whatsapp_sms(str(user.phone_number), message, code_id=code.id)
        elif email == True:
            MailerService.send_verification_code_email(email=user.email, code=code.code)
        elif phone_number == "+996770413928":
            AzamatMessageService.save_in_model(message, phone_number)
        elif phone_number == "+996555214242":
            AzamatMessageService.save_in_model(message, phone_number)
        # elif phone_number == "+971585333939":
        #     AzamatMessageService.save_in_model(message, phone_number)
        elif phone_number == "+996554121621":
            AzamatMessageService.save_in_model(message, phone_number)
        # elif phone_number == "+971585939381":
        #     AzamatMessageService.save_in_model(message, phone_number)
        elif phone_number.startswith("+996"):
            MessageServiceNIKITA.send_sms(numbers=[user.phone_number], message=message, sms_id=sms_id, code_id=code.id,
                                          ip_addr=ip_addr)
        elif phone_number.startswith("+971"):
            MessageServiceMessageBird.send_sms(number=str(user.phone_number), code=message, code_id=code.id,
                                               ip_addr=ip_addr, voice=True, voice_code=code.code)
        else:
            # MessageServiceTwilio.send_sms(str(user.phone_number), message, code_id=code.id, ip_addr=ip_addr)
            MessageServiceMessageBird.send_sms(number=str(user.phone_number), code=message, code_id=code.id,
                                               ip_addr=ip_addr, voice=False)
        return code

    @classmethod
    def validate(cls, code: str, phone_number: str):
        try:
            temporary_code = cls.model.objects.get(code=code, user__phone_number=phone_number, is_used=False)

            if temporary_code.expiration_datetime < timezone.now():
                slack.bot_2(f'Code time expired for {phone_number}\n'
                            f'link code: https://apofiz.com/admin/users/temporarycode/{temporary_code.id}/change/\n'
                            f'============================')
                raise ValidationException(_('Code time expired'))

            cls.model.objects.filter(user__phone_number=phone_number).update(is_used=True)

        except cls.model.DoesNotExist:
            slack.bot_2(f'Entered incorrect code for {phone_number}\n'
                        f'============================')
            raise ValidationException(_('Code not found'))


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


class DeliveryAddressesService:
    model = DeliveryAddress

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('DeliveryAddress not found'))

    @classmethod
    def get_addresses_of_user(cls, user: User) -> QuerySet:
        return DeliveryAddress.objects.filter(user=user).order_by('-by_default', 'id')

    @classmethod
    def create(cls, user:User, longitude, latitude, **kwargs):
        try:
            if longitude and latitude:
                point = Point(longitude, latitude)
            else:
                point = None

            kwargs['location'] = point
            kwargs['user'] = user

            created = cls.model.objects.create(**kwargs)
            return created
        except Exception as e:
            raise BadRequestException(_(f'Could not add delivery address , {e}'))

    @classmethod
    def set_default_delivery_address(cls, address_id: int, user: User):
        address = cls.get(id=address_id, user=user)

        DeliveryAddress.objects.filter(user=user).exclude(id=address.id).update(by_default=False)

        address.by_default = True
        address.save()


class TemporaryPhoneNumberService:
    model = TemporaryPhoneNumber

    @classmethod
    def get(cls, **filters):
        try:
            return cls.model.objects.get(**filters)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('Temporary phone number not found'))

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
                raise ValidationException(_('Limit exceeded'))

            code = cls.model.objects.create(user=user, phone_number=phone_number)

            message = SMS_CODE_MESSAGE.format(code.code)
            sms_id = f'{user.id}{code.code}'
            MessageServiceNIKITA.send_sms(numbers=[phone_number], message=message, sms_id=sms_id, code_id=code.id)

        except IntegrityError:
            raise IntegrityException(_('Error while creating temporary code for new phone_number'))

    @classmethod
    def validate_code_and_phone_number(cls, code: str, phone_number: str):
        try:
            temporary_code = cls.model.objects.get(code=code, user__phone_number=phone_number)

            if temporary_code.expiration_datetime < timezone.now():
                raise ValidationException(_('Code expired'))

            cls.model.objects.filter(user__phone_number=phone_number).delete()

        except cls.model.DoesNotExist:
            raise ValidationException(_('Code not found'))

    @classmethod
    def validate_phone_number(cls, phone_number: str):
        try:
            cls.model.objects.filter(user__phone_number=phone_number).delete()
        except cls.model.DoesNotExist:
            raise ValidationException(_('Wrong phone number'))

