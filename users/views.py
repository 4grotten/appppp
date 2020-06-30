from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    RegisterAuthSerializer, TemporaryCodeSerializer,
    ResendTemporaryCodeSerializer, LoginSerializer,
    ProfileUpdateSerializer, ProfileSerializer, SetPasswordSerializer, UserChangePasswordSerializer,
    ForgotPasswordSerializer, PhoneNumberSerializer, SocialNetworkContactSerializer
)
from .services import UserService, TemporaryCodeService, PhoneNumberService, SocialNetworkContactService


class RegisterAuthAPIView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        serializer = RegisterAuthSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={
                    'message': 'Something went wrong',
                    'errors': serializer.errors
                },
                status=status.HTTP_406_NOT_ACCEPTABLE
            )

        phone_number = serializer.validated_data.get('phone_number')

        if not UserService.filter(phone_number=phone_number).exists():
            user = UserService.create(phone_number=phone_number)
            TemporaryCodeService.create_and_send(user=user)

            return Response(data={
                'message': 'User has successfully created',
                'is_new_user': user.is_new_user
            })

        user = UserService.get(phone_number=phone_number)

        if user.is_new_user:
            TemporaryCodeService.create_and_send(user=user)

        return Response(data={
            'message': 'User found',
            'is_new_user': user.is_new_user
        })


class VerifyTemporaryCodeAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = TemporaryCodeSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        code = serializer.validated_data.get('code')
        phone_number = serializer.validated_data.get('phone_number')

        TemporaryCodeService.validate(code=code, phone_number=phone_number)

        user = UserService.get(phone_number=phone_number)

        token, created = Token.objects.get_or_create(user=user)

        return Response(data={
            'message': 'Successfully validated',
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
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        phone_number = serializer.validated_data.get('phone_number')
        user = UserService.get(phone_number=phone_number)

        TemporaryCodeService.create_and_send(user=user)

        return Response(data={
            'message': 'Code has successfully sent'
        }, status=status.HTTP_200_OK)


class ProfileInitialAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, many=False, context={'request': request})

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = UserService.init_profile(
            user=request.user,
            avatar_id=serializer.validated_data.get('avatar_id'),
            username=serializer.validated_data.get('username'),
            date_of_birth=serializer.validated_data.get('date_of_birth'),
            email=serializer.validated_data.get('email'),
            gender=serializer.validated_data.get('gender'),
            full_name=serializer.validated_data.get('full_name')
        )

        return Response(ProfileSerializer(user, context={'request': request}).data, status=status.HTTP_200_OK)


class SetPasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = SetPasswordSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        UserService.set_password(user=request.user, password=serializer.validated_data.get('password'))

        return Response(data={
            'message': 'You have successfully set password'
        }, status=status.HTTP_200_OK)


class LoginAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        user = authenticate(**serializer.validated_data)

        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            user_data = ProfileSerializer(user, context={'request': request}).data
            return Response(data={
                'message': 'Successfully logged in',
                'token': token.key,
                'user': user_data
            }, status=status.HTTP_200_OK)

        return Response(data={
            'message': 'Wrong credentials',
            'errors': {}
        }, status=status.HTTP_400_BAD_REQUEST)


class UserChangePasswordAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = UserChangePasswordSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        UserService.change_password(
            user=request.user,
            old_password=serializer.validated_data.get('old_password', None),
            new_password=serializer.validated_data.get('new_password', None)
        )

        return Response(data={'message': 'Password has successfully changed'}, status=status.HTTP_200_OK)


class ForgotPasswordAPIView(APIView):
    authentication_classes = ()
    permission_classes = ()

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
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
        #            raise ValidationException('Invalid input')

        return Response(data={
            'message': 'Code sent'
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
        numbers = PhoneNumberService.update_phone_numbers(user=request.user, numbers=request.data)
        data = PhoneNumberSerializer(numbers, many=True).data
        return Response(data={
            'message': 'Successfully updated',
            'networks': data
        }, status=status.HTTP_200_OK)


class UserNetworksListAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, **kwargs):
        networks = SocialNetworkContactService.get_networks_of_user(user_id=kwargs['pk'])
        data = SocialNetworkContactSerializer(networks, many=True).data
        return Response(data)


class UserSocialNetworksUpdateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        networks = SocialNetworkContactService.update_social_networks(user=request.user, urls=request.data)
        data = SocialNetworkContactSerializer(networks, many=True).data
        return Response(data={
            'message': 'Successfully updated',
            'networks': data
        }, status=status.HTTP_200_OK)
