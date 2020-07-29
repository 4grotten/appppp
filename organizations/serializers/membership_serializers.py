from rest_framework import serializers

from organizations.models import Membership, Role
from organizations.serializers.card_serializers import UserFilteredPrimaryKeyRelatedField
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
