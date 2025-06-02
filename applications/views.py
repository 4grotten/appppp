from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _

from applications.serializers import UserAppCreateSerializer, UserAppDetailedSerializer
from applications.services import UserAppService


class UserAppCreateView(CreateAPIView):
    permission_classes = (IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        serializer = UserAppCreateSerializer(data=request.data, context={'request': request})

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        organization = UserAppService.create_application(**serializer.validated_data)

        data = UserAppDetailedSerializer(organization, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)
