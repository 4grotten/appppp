from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RegisterAuthSerializer
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
