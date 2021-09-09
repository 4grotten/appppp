from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.exceptions import NotAcceptableException, ObjectNotFoundException
from .constants import CHANGE_AUTH_NUMBER_TYPE, REGISTER_AUTH_TYPE
from .serializers import (
    RegisterAuthSerializer, TemporaryCodeSerializer, LoginSerializer,
    ResendTemporaryCodeSerializer, ProfileUpdateSerializer, ProfileSerializer,
    SetPasswordSerializer, UserChangePasswordSerializer, ForgotPasswordSerializer,
    SendCodeToNewNumberSerializer, PhoneNumberEditSerializer, SocialNetworkEditSerializer,
    PhoneNumberSerializer, SocialNetworkContactSerializer, ChangeAndValidateNewNumberSerializer,
)
from .services import (
    UserService, TemporaryCodeService, PhoneNumberService, SocialNetworkContactService, TemporaryPhoneNumberService
)


class RegisterAuthAPIView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        serializer = RegisterAuthSerializer(data=request.data)

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

        if not UserService.filter(phone_number=phone_number).exists():
            user = UserService.create(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user)

            return Response(data={
                'message': gettext_lazy('User has successfully created'),
                'is_new_user': user.is_new_user,
                'token': None
            })

        user = UserService.get(phone_number=phone_number)

        if user.is_new_user:
            if TemporaryCodeService.filter(user=user, is_used=True).exists():
                token, _ = Token.objects.get_or_create(user=user)
            else:
                TemporaryCodeService.create_and_send(user=user)

        return Response(data={
            'message': gettext_lazy('User found'),
            'is_new_user': user.is_new_user,
            'token': token.key if token else None
        })


class VerifyTemporaryCodeAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = TemporaryCodeSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        code = serializer.validated_data.get('code')
        phone_number = serializer.validated_data.get('phone_number')

        TemporaryCodeService.validate(code=code, phone_number=phone_number)

        user = UserService.get(phone_number=phone_number)

        token, created = Token.objects.get_or_create(user=user)

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

        if resend_type == CHANGE_AUTH_NUMBER_TYPE:
            temporary_codes = TemporaryPhoneNumberService.filter(phone_number=phone_number)
            if not temporary_codes:
                raise ObjectNotFoundException(gettext_lazy('You can not resend'))

            temporary_code = temporary_codes.last()

            TemporaryPhoneNumberService.create(user=temporary_code.user, phone_number=phone_number)

        elif resend_type == REGISTER_AUTH_TYPE:
            user = UserService.get(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user)

        return Response(data={
            'message': gettext_lazy('Code has successfully sent')
        }, status=status.HTTP_200_OK)


class ProfileInitialAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, many=False, context={'request': request})

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
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': gettext_lazy('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = authenticate(**serializer.validated_data)

        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
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
        # token_key = request.headers['Authorization'].split()[1]
        # Token.objects.filter(key=token_key).delete()

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

        user = UserService.get(phone_number=serializer.validated_data.get('phone_number'))
        TemporaryCodeService.create_and_send(user=user)

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
        TemporaryCodeService.create_and_send(user=request.user)

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
