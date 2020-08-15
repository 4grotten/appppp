from rest_framework import serializers

from organizations.models import Membership, Role, Organization
from organizations.serializers.attendance_serializers import MembershipListAttendanceSerializer
from organizations.serializers.card_serializers import UserFilteredPrimaryKeyRelatedField
from organizations.services.attendance_services import AttendanceService
from users.models import User
from users.serializers import EmployeeSerializer


class RoleBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ('id', 'title',)


class RoleSerializer(serializers.ModelSerializer):
    can_sale = serializers.BooleanField()
    can_check_attendance = serializers.BooleanField()
    can_see_stats = serializers.BooleanField()
    can_edit_organization = serializers.BooleanField()
    can_send_message = serializers.BooleanField()
    can_edit_partner = serializers.BooleanField()

    class Meta:
        model = Role
        fields = (
            'id', 'title', 'can_sale', 'can_check_attendance', 'can_see_stats',
            'can_edit_organization', 'can_send_message', 'can_edit_partner'
        )


class RoleCreateSerializer(serializers.ModelSerializer):
    organization = UserFilteredPrimaryKeyRelatedField(write_only=True)
    can_sale = serializers.BooleanField()
    can_check_attendance = serializers.BooleanField()
    can_see_stats = serializers.BooleanField()
    can_edit_organization = serializers.BooleanField()
    can_send_message = serializers.BooleanField()
    can_edit_partner = serializers.BooleanField()

    class Meta:
        model = Role
        fields = (
            'id', 'title', 'organization', 'can_sale', 'can_check_attendance', 'can_see_stats',
            'can_edit_organization', 'can_send_message', 'can_edit_partner'
        )


class MembershipSerializer(serializers.ModelSerializer):
    role = RoleBriefSerializer()
    user = EmployeeSerializer()

    class Meta:
        model = Membership
        fields = ('id', 'role', 'user',)


class MembershipListSerializer(serializers.ModelSerializer):
    role = RoleBriefSerializer()
    user = EmployeeSerializer()
    attendance = serializers.SerializerMethodField()

    def get_attendance(self, membership: Membership):
        latest = AttendanceService.get_latest_attendance(employee=membership.user, organization=membership.organization)
        if latest is None:
            return None
        return MembershipListAttendanceSerializer(latest).data

    class Meta:
        model = Membership
        fields = ('id', 'role', 'user', 'attendance',)


class MembershipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('role', 'user', 'organization',)


class MembershipUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ('role',)


class TransferOwnershipSerializer(serializers.Serializer):
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.filter(is_active=True))
    new_owner = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(is_active=True))
