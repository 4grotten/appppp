from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy
from requests import get
from rest_framework import status
from rest_framework.exceptions import Throttled
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from transliterate.utils import _

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from common.models import UmaiWallet, BlockedIps, TemporaryCodeSwitcher
from common.services import slack
from common.services.umai import Umai
from organizations.models import Subscription, Organization
from .constants import CHANGE_AUTH_NUMBER_TYPE, REGISTER_AUTH_TYPE, DEVICE_TYPES, WHATSAPP_AUTH_TYPE, VOICE_AUTH_TYPE, \
    EMAIL_AUTH_TYPE
from .models import MyOwnToken, User
from .serializers import (
    RegisterAuthSerializer, TemporaryCodeSerializer, LoginSerializer,
    ResendTemporaryCodeSerializer, ProfileUpdateSerializer, ProfileSerializer,
    SetPasswordSerializer, UserChangePasswordSerializer, ForgotPasswordSerializer,
    SendCodeToNewNumberSerializer, PhoneNumberEditSerializer, SocialNetworkEditSerializer,
    PhoneNumberSerializer, SocialNetworkContactSerializer, ChangeAndValidateNewNumberSerializer, MyOwnTokenSerializer,
    MyOwnTokenExpiredTimeSerializer,
)
from .services import (
    UserService, TemporaryCodeService, PhoneNumberService, SocialNetworkContactService, TemporaryPhoneNumberService, MyOwnTokenService
)
from .throttle.throttle import UserLoginRateThrottle
from user_agents import parse

class RegisterAuthAPIView(APIView):
    permission_classes = ()
    authentication_classes = ()
    throttle_classes = (UserLoginRateThrottle,)

    def throttled(self, request, wait):
        raise Throttled(detail={
            "message": "recaptcha_required",
        })

    def post(self, request):
        serializer = RegisterAuthSerializer(data=request.data)

        ip = request.META.get('REMOTE_ADDR', '')
        if BlockedIps.objects.filter(ip_address=ip).first():
            return Response(status=403, data={'message': "Forbidden"})

        if not serializer.is_valid():
            return Response(
                data={
                    'message': gettext_lazy('Invalid input'),
                    'errors': serializer.errors
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        token = None
        phone_number = serializer.validated_data.get('phone_number')
        temporary_code_enabled = TemporaryCodeSwitcher.objects.last().is_enable

        if not UserService.filter(phone_number=phone_number).exists():
            ip = request.META.get('REMOTE_ADDR', '')
            user = UserService.create(phone_number=phone_number)

            if temporary_code_enabled:
                TemporaryCodeService.create_and_send(user=user, ip_addr=ip)
            else:
                token = MyOwnTokenService.get_or_create_token(user=user, request=request)

            return Response(data={
                'message': gettext_lazy('User has successfully created'),
                'is_new_user': user.is_new_user,
                'token': token,
                'temporary_code_enabled': temporary_code_enabled
            })


        user = UserService.get(phone_number=phone_number)

        if not user.is_active:
            return Response(
                data={
                    'message': _('User deleted')
                },
                status=status.HTTP_403_FORBIDDEN
            )

        if user.is_new_user:
            if TemporaryCodeService.filter(user=user, is_used=True).exists() or not temporary_code_enabled:
                token = MyOwnTokenService.get_or_create_token(user=user, request=request)
            else:
                ip = request.META.get('REMOTE_ADDR', '')
                TemporaryCodeService.create_and_send(user=user, ip_addr=ip)

        return Response(data={
            'message': gettext_lazy('User found'),
            'is_new_user': user.is_new_user,
            'token': token.key if token else None,
            'email': True if user.email else False,
        })


class VerifyTemporaryCodeAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = TemporaryCodeSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        code = serializer.validated_data.get('code')
        phone_number = serializer.validated_data.get('phone_number')

        TemporaryCodeService.validate(code=code, phone_number=phone_number)

        user = UserService.get(phone_number=phone_number)

        try:
            token = MyOwnToken.objects.get(user=user, is_active=True, ip=request.META.get('REMOTE_ADDR'))
        except MyOwnToken.DoesNotExist:
            token = MyOwnToken.objects.create(user=user, ip=request.META.get('REMOTE_ADDR'))
            token.save()
        slack.bot(f'User {user} successfully validated\n'
                  f'============================')

        return Response(data={
            'message': gettext_lazy('Successfully validated'),
            'token': token.key if token else None,
            'is_new_user': user.is_new_user
        }, status=status.HTTP_200_OK)


class ResendTemporaryCodeAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = ResendTemporaryCodeSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        resend_type = serializer.validated_data.get('type')
        phone_number = serializer.validated_data.get('phone_number')
        ip = request.META.get('REMOTE_ADDR', '')
        if resend_type == CHANGE_AUTH_NUMBER_TYPE:
            temporary_codes = TemporaryPhoneNumberService.filter(phone_number=phone_number)
            if not temporary_codes:
                raise ObjectNotFoundException(gettext_lazy('You can not resend'))

            temporary_code = temporary_codes.last()

            TemporaryPhoneNumberService.create(user=temporary_code.user, phone_number=phone_number)

        elif resend_type == REGISTER_AUTH_TYPE:
            user = UserService.get(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user, ip_addr=ip)

        elif resend_type == WHATSAPP_AUTH_TYPE:
            user = UserService.get(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user, whatsapp=True, ip_addr=ip)

        elif resend_type == EMAIL_AUTH_TYPE:
            user = UserService.get(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user, email=True, ip_addr=ip)

        elif resend_type == VOICE_AUTH_TYPE:
            # ToDo voice auth type
            pass

        return Response(data={
            'message': gettext_lazy('Code has successfully sent')
        }, status=status.HTTP_200_OK)


class ProfileInitialAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ProfileUpdateSerializer(data=UserService.get_data_with_valid_location(request), many=False, context={'request': request})

        is_new_in_begin = request.user.is_new_user
        if is_new_in_begin:
            MyOwnTokenService.save_device_info(request=request, serializer=serializer)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = UserService.init_profile(
            user=request.user,
            avatar_id=serializer.validated_data.get('avatar_id'),
            username=serializer.validated_data.get('username', None),
            date_of_birth=serializer.validated_data.get('date_of_birth', None),
            gender=serializer.validated_data.get('gender'),
            full_name=serializer.validated_data.get('full_name'),
            email=serializer.validated_data.get('email', None),
        )

        registration = UmaiWallet.objects.last()
        device_type = serializer.validated_data.get('device_type')
        if device_type in DEVICE_TYPES and registration and registration.is_accepted and \
                str(user.phone_number).startswith("+996") and is_new_in_begin:
            Umai(str(user.phone_number), wallet=registration).commit_payment()
        if user.full_name != None:
            apofiz_org = Organization.objects.get(title='Apofiz.com')
            subscription, created = Subscription.objects.get_or_create(user=user, organization=apofiz_org)
        return Response(ProfileSerializer(user, context={'request': request}).data, status=status.HTTP_200_OK)


class SetPasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        UserService.set_password(user=request.user, password=serializer.validated_data.get('password'))

        return Response(data={
            'message': gettext_lazy('You have successfully set password')
        }, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=UserService.get_data_with_valid_location(request))

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = authenticate(**serializer.validated_data)

        if user is not None:
            device_info = MyOwnTokenService.get_device_info(serializer=serializer, request=request)
            location = UserService.get_location_info(serializer=serializer)

            token = MyOwnTokenService.get_or_create_token(user=user, request=request, location=location, device_info=device_info)

            user_data = ProfileSerializer(user, context={'request': request}).data
            return Response(data={
                'message': gettext_lazy('Successfully logged in'),
                'token': token.key,
                'user': user_data
            }, status=status.HTTP_200_OK)

        return Response(data={
            'message': gettext_lazy('Wrong credentials'),
            'errors': {}
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        # ToDo: MULTI-TOKEN AUTH
        token_key = request.headers['Authorization'].split()[1]
        MyOwnToken.objects.filter(key=token_key).update(is_active=False)

        return Response(data={
            'message': gettext_lazy('Successfully logged out'),
        }, status=status.HTTP_200_OK)


class UserChangePasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = UserChangePasswordSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        UserService.change_password(
            user=request.user,
            old_password=serializer.validated_data.get('old_password', None),
            new_password=serializer.validated_data.get('new_password', None)
        )

        return Response(data={'message': gettext_lazy('Password has successfully changed')}, status=status.HTTP_200_OK)


class ForgotPasswordAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        ip = request.META.get('REMOTE_ADDR', '')
        user = UserService.get(phone_number=serializer.validated_data.get('phone_number'))
        TemporaryCodeService.create_and_send(user=user, ip_addr=ip)

        #        input_type = serializer.validated_data.get('type')

        #        if input_type == PHONE_NUMBER_TYPE:
        #            user = UserService.get(phone_number=serializer.validated_data.get('phone_number'))
        #            TemporaryCodeService.create_and_send(user=user)
        #        elif input_type == EMAIL_TYPE:
        #            user = UserService.get(email=serializer.validated_data.get('email'))
        #            # TODO send code to email
        #        else:
        #            raise ValidationException(_('Invalid input'))

        return Response(data={
            'message': gettext_lazy('Code sent')
        }, status=status.HTTP_200_OK)


class CurrentUserAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        return Response(ProfileSerializer(user, context={'request': request}).data)


class UserPhonesListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        numbers = PhoneNumberService.get_numbers_of_user(user_id=kwargs['pk'])
        data = PhoneNumberSerializer(numbers, many=True).data
        return Response(data)


class UserPhoneNumbersUpdateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = PhoneNumberEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        numbers = PhoneNumberService.update_phone_numbers(user=request.user,
                                                          numbers=serializer.validated_data['phone_numbers'])
        data = PhoneNumberSerializer(numbers, many=True).data
        return Response(data={
            'message': gettext_lazy('Successfully updated'),
            'numbers': data
        }, status=status.HTTP_200_OK)


class UserSocialNetworksListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        networks = SocialNetworkContactService.get_networks_of_user(user_id=kwargs['pk'])
        data = SocialNetworkContactSerializer(networks, many=True).data
        return Response(data)


class UserSocialNetworksUpdateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SocialNetworkEditSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        networks = SocialNetworkContactService.update_social_networks(user=request.user,
                                                                      urls=serializer.validated_data['networks'])
        data = SocialNetworkContactSerializer(networks, many=True).data
        return Response(data={
            'message': gettext_lazy('Successfully updated'),
            'networks': data
        }, status=status.HTTP_200_OK)


class ValidateOldNumberAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        ip = request.META.get('REMOTE_ADDR', '')
        TemporaryCodeService.create_and_send(user=request.user, ip_addr=ip)

        return Response(data={
            'message': gettext_lazy('Code sent to old number and email')
        })


class ChangeAndVerifyNewNumber(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ChangeAndValidateNewNumberSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        old_phone_number = serializer.validated_data.get('old_phone_number')

        user = UserService.get(phone_number=old_phone_number)

        if user != request.user:
            raise NotAcceptableException(gettext_lazy('You have not permission to do this operation'))

        TemporaryPhoneNumberService.validate(
            code=serializer.validated_data.get('code'), phone_number=old_phone_number
        )

        UserService.change_phone_number(
            user=user, new_phone_number=serializer.validated_data.get('new_phone_number')
        )

        return Response(data={
            'message': gettext_lazy('You have successfully changed auth number')
        })


class SendCodeToNewNumberAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SendCodeToNewNumberSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        TemporaryPhoneNumberService.create(
            user=request.user,
            phone_number=serializer.validated_data.get('phone_number')
        )

        return Response(data={
            'message': gettext_lazy('Code sent to new phone number')
        })


class GetEmailUserAPIView(APIView):

    def post(self, request):
        serializer = PhoneNumberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    'message': gettext_lazy('Invalid input'),
                    'errors': serializer.errors
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )
        phone_number = serializer.validated_data['phone_number']
        email = UserService.get_user_email_by_phone_number(phone_number=phone_number)
        return Response({'email': email})


class MyOwnTokenChangeExpiredTimeView(APIView):
    def post(self, request, **kwargs):
        serializer = MyOwnTokenExpiredTimeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    'message': gettext_lazy('Invalid input'),
                    'errors': serializer.errors
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )
        expired_time = serializer.validated_data['expired_time_choice']
        token = MyOwnToken.objects.get(id=self.kwargs['pk'])
        token.expired_time_choice = expired_time
        token.save()
        return Response({'success': True})


class MyOwnTokenListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyOwnTokenSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return MyOwnToken.objects.filter(user=user, is_active=True).order_by('-log_time')


class MyOwnTokenRetrieveDestroyView(RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyOwnTokenSerializer

    def get_object(self):
        try:
            return MyOwnToken.objects.get(id=self.kwargs['pk'])
        except MyOwnToken.DoesNotExist:
            return Response(
                data={
                    "Error": _("Invalid id"),
                }, status=status.HTTP_400_BAD_REQUEST
            )

    def destroy(self, request, *args, **kwargs):
        MyOwnToken.objects.filter(id=self.kwargs['pk']).update(is_active=False)
        return Response({'message': 'Token deactivated'}, status=status.HTTP_200_OK)


class DestroyAllTokens(DestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyOwnTokenSerializer

    def destroy(self, request, *args, **kwargs):
        MyOwnToken.objects.filter(user=self.request.user).update(is_active=False)
        return Response({'message': 'All tokens of user deactivated'}, status=status.HTTP_200_OK)


class AuthorisationHistoryListView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = MyOwnTokenSerializer
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        return MyOwnToken.objects.filter(user=user, is_active=False).order_by('-log_time')

class DeactivateUserProfile(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            user = self.request.user
            user.is_active = False
            user.save()
            return Response(
                data={
                    "Success": True,
                }, status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                data={
                    "Error": _("User does not exists"),
                }, status=status.HTTP_400_BAD_REQUEST
            )
