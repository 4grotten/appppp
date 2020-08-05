from django.db import transaction
from fcm_django.api.rest_framework import FCMDeviceSerializer
from fcm_django.models import FCMDevice
from rest_framework import serializers

from common.exceptions import IntegrityException
from notifications.models import Notification, NotificationSetting
from organizations.serializers.organization_serializers import OrganizationNotificationInfo
from users.serializers import ProfileSerializer


class NotificationSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer(many=False, allow_null=True)
    organization = OrganizationNotificationInfo(allow_null=True)

    class Meta:
        model = Notification
        fields = ('id', 'created_at', 'updated_at', 'sender', 'extra_data',
                  'mode', 'title', 'description', 'is_read', 'organization', 'type')


class CustomFCMDeviceSerializer(FCMDeviceSerializer):
    def create(self, validated_data):
        with transaction.atomic():
            fcm_device = FCMDevice.objects.create(**validated_data)
            try:

                if NotificationSetting.objects.filter(user=fcm_device.user).exists():
                    notification_setting = NotificationSetting.objects.get(user=fcm_device.user)
                    notification_setting.fcm_device.add(fcm_device)

                else:
                    notification_setting = NotificationSetting.objects.create(
                        user=fcm_device.user
                    )
                    notification_setting.fcm_device.add(fcm_device)
            except Exception as e:
                raise IntegrityException('Error while creating notification setting: {e}'.format(e=str(e)))

            return fcm_device


class NotificationSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationSetting
        fields = ('id', 'discount_notifications', 'private_notifications', 'organization_notifications')
        extra_kwargs = {"id": {"read_only": True, "required": False}}
