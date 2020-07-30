from rest_framework import serializers

from notifications.models import Notification
from organizations.serializers.organization_serializers import OrganizationNotificationInfo
from users.serializers import ProfileSerializer


class NotificationSerializer(serializers.ModelSerializer):
    sender = ProfileSerializer(many=False, allow_null=True)
    organization = OrganizationNotificationInfo(allow_null=True)

    class Meta:
        model = Notification
        fields = ('id', 'created_at', 'updated_at', 'sender',
                  'mode', 'title', 'description', 'is_read', 'organization')
