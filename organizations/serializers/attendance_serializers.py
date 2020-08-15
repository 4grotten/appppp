from rest_framework import serializers

from organizations.models import Attendance
from users.serializers import ProfileBriefSerializer


class CreateAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ('user', 'organization',)


class AttendanceSerializer(serializers.ModelSerializer):
    arrival_checked_by = ProfileBriefSerializer()
    departure_checked_by = ProfileBriefSerializer()

    class Meta:
        model = Attendance
        fields = ('id', 'arrival_time', 'arrival_checked_by', 'departure_time', 'departure_checked_by')


class MembershipListAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = ('is_active', 'arrival_time', 'departure_time')


class GroupAttendanceSerializer(serializers.Serializer):
    date = serializers.DateField()
    attendances = AttendanceSerializer(many=True)
