from rest_framework import serializers

from notifications.models import Notification
from users.serializers import ProfileSerializer


class NotificationSerializer(serializers.ModelSerializer):
    recipient = ProfileSerializer(many=False)
    sender = ProfileSerializer(many=False, allow_null=True)

    class Meta:
        model = Notification
        fields = ('id', 'recipient', 'sender',
                  'mode', 'title', 'description', 'is_read')
