from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django_filters.rest_framework import DjangoFilterBackend
from fcm_django.api.rest_framework import AuthorizedMixin, FCMDeviceViewSet
from fcm_django.models import FCMDevice
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import NotificationFilter
from .serializers import (
    NotificationSerializer,
    CustomFCMDeviceSerializer,
    NotificationSettingSerializer,
    FCMDeviceSettingsSerializer,
)
from .services import (
    NotificationService,
    NotificationSettingService,
    FCMDeviceSettingsService,
)


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
        notification_setting = NotificationSettingService.get_or_create(
            user=request.user
        )

        return Response(self.serializer_class(notification_setting, many=False).data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )

        notification_setting = NotificationSettingService.get_or_create(
            user=request.user
        )

        updated_notification_setting = NotificationSettingService.update(
            notification_setting=notification_setting, **serializer.validated_data
        )

        return Response(
            self.serializer_class(updated_notification_setting, many=False).data
        )


class NotificationsCountAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            data={
                "count": NotificationService.get_user_notifications_count(
                    user=request.user
                )
            }
        )

    def post(self, request):
        NotificationService.do_read_notifications(user=request.user)

        return Response(data={"message": _("Success")})


class FCMDeviceSettingsAPIView(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FCMDeviceSettingsSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(
                data={"message": _("Invalid input"), "errors": serializer.errors},
                status=status.HTTP_406_NOT_ACCEPTABLE,
            )
        FCMDeviceSettingsService.create(**serializer.validated_data, user=request.user)

        return Response(data={"message": _("Success")})


class DeleteFCMDeviceDuplicatesAPIView(APIView):
    """
    APIView to delete duplicates in FCMDevice model based on registration_id.
    """

    def post(self, request):
        try:
            # Step 1: Group FCMDevices by registration_id and find duplicates
            devices = (
                FCMDevice.objects.values("registration_id")
                .annotate(duplicate_count=Count("id"))
                .filter(duplicate_count__gt=1)
            )

            deleted_count = 0

            for device_group in devices:
                reg_id = device_group["registration_id"]

                # Step 2: Find all devices with the same registration_id
                duplicates = FCMDevice.objects.filter(registration_id=reg_id).order_by(
                    "-created_at"
                )

                # Step 3: Keep the first device and delete the others
                if duplicates.count() > 1:
                    primary_device = duplicates.first()  # The device to keep
                    other_devices = duplicates[1:]  # The devices to delete

                    # Delete all other duplicate devices
                    for other_device in other_devices:
                        other_device.delete()
                        deleted_count += 1

            return Response(
                {
                    "message": f"Successfully deleted {deleted_count} duplicate FCMDevice entries."
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
