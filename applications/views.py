from rest_framework import status
from rest_framework.generics import CreateAPIView, ListCreateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.views import APIView

from applications.models import AddedApp, UserApp
from applications.serializers import UserAppCreateSerializer, UserAppDetailedSerializer, UserAppListSerializer, \
    UserAppUpdateSerializer
from applications.services import UserAppService
from common.exceptions import NotAcceptableException
from common.utils import method_permission_classes


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


class UserAppRetrieveUpdateView(RetrieveUpdateAPIView):
    serializer_class = UserAppDetailedSerializer
    queryset = UserApp.objects.all()

    def get(self, request, *args, **kwargs):
        instance = self.get_object()

        context = {
            'request': request,
        }

        serializer = self.serializer_class(instance, context=context)
        return Response(serializer.data)

    @method_permission_classes((IsAuthenticated,))
    def put(self, request, *args, **kwargs):
        serializer = UserAppUpdateSerializer(data=request.data, many=False)

        if not serializer.is_valid():
            return Response(data={
                'message': _('Invalid input'),
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        application = UserAppService.get(id=kwargs['pk'])
        if application.owner != request.user:
            raise NotAcceptableException(_('No rights to edit application'))
        validated_data = serializer.validated_data
        image_id = validated_data.pop('image_id')
        updated_application = UserAppService.update(application=application, image_id=image_id,
                                                    validated_data=validated_data)
        return Response(self.serializer_class(updated_application, context={'request': request}).data)


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
