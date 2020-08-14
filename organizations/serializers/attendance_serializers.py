from rest_framework import serializers

from organizations.models import Attendance
from users.serializers import ProfileBriefSerializer


class CreateAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ('user', 'organization',)
