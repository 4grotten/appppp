from rest_framework import status
from rest_framework.generics import CreateAPIView, ListCreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView

from applications.models import AddedApp
from applications.serializers import UserAppCreateSerializer, UserAppDetailedSerializer, UserAppListSerializer
from applications.services import UserAppService


class UserAppListCreateView(ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        user = request.user

        my_apps = UserAppService.filter(owner=user)

        added_apps = UserAppService.filter(addedapp__user=user).exclude(owner=user)

        return Response({
            'my_apps': UserAppListSerializer(my_apps, many=True, context={'request': request}).data,
            'my_added_apps': UserAppListSerializer(added_apps, many=True, context={'request': request}).data
        })

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


class ToggleUserAppView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        user_app = UserAppService.get(id=kwargs['pk'])

        if user_app.owner == request.user:
            return Response({"detail": "You cannot add your own app."}, status=status.HTTP_400_BAD_REQUEST)

        added_app, created = AddedApp.objects.get_or_create(
            user=request.user,
            user_app=user_app
        )

        if not created:
            added_app.delete()
            return Response({"message": "Successfully deleted"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "Successfully added"}, status=status.HTTP_201_CREATED)
