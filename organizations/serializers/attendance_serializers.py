from rest_framework import serializers

from organizations.models import Attendance


class RecordAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ('user', 'organization',)
