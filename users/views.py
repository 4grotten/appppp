from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterAuthSerializer, TemporaryCodeSerializer, ResendTemporaryCodeSerializer, \
    ProfileUpdateSerializer, ProfileSerializer
from .services import UserService, TemporaryCodeService


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
            TemporaryCodeService.create(user=user)

            return Response(data={
                'message': 'User has successfully created',
                'is_new_user': user.is_new_user
            })

        user = UserService.get(phone_number=phone_number)

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

        token = None

        if user.is_new_user:
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

        TemporaryCodeService.create(user=user)

        return Response(data={
            'message': 'Code has successfully sent'
        }, status=status.HTTP_200_OK)


class ProfileInitialAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = ProfileUpdateSerializer(data=request.data, many=False)

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

        return Response(ProfileSerializer(user).data, status=status.HTTP_200_OK)
