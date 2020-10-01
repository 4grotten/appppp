from django_filters.rest_framework import DjangoFilterBackend
from fcm_django.api.rest_framework import AuthorizedMixin, FCMDeviceViewSet
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import NotificationFilter
from .serializers import NotificationSerializer, CustomFCMDeviceSerializer, NotificationSettingSerializer, \
    FCMDeviceSettingsSerializer
from .services import NotificationService, NotificationSettingService, FCMDeviceSettingsService


class NotificationListAPIView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_class = NotificationFilter

    def get_queryset(self):
        return NotificationService.get_own_notifications(user=self.request.user)


class CustomFCMDeviceAuthorizedViewSet(AuthorizedMixin, FCMDeviceViewSet):
    serializer_class = CustomFCMDeviceSerializer


class NotificationSettingAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationSettingSerializer

    def get(self, request):
        notification_setting = NotificationSettingService.get_or_create(user=request.user)

        return Response(self.serializer_class(notification_setting, many=False).data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)

        notification_setting = NotificationSettingService.get_or_create(user=request.user)

        updated_notification_setting = NotificationSettingService.update(
            notification_setting=notification_setting,
            **serializer.validated_data
        )

        return Response(self.serializer_class(updated_notification_setting, many=False).data)


class NotificationsCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(data={
            'count': NotificationService.get_user_notifications_count(user=request.user)
        })

    def post(self, request):
        NotificationService.do_read_notifications(user=request.user)

        return Response(data={
            'message': 'Success'
        })


class FCMDeviceSettingsAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FCMDeviceSettingsSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(data={
                'message': 'Invalid input',
                'errors': serializer.errors
            }, status=status.HTTP_406_NOT_ACCEPTABLE)
        device_settings = FCMDeviceSettingsService.update(**serializer.validated_data, user=request.user)

        return Response(data={
            'message': 'Success'
        })
