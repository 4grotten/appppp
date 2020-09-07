from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Organization
from organizations.services.attendance_services import AttendanceService
from organizations.services.organization_services import OrganizationService
from .constants import RESEND_CODE_CHOICES
from .models import PhoneNumber, SocialNetworkContact

User = get_user_model()


class RegisterAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class TemporaryCodeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    phone_number = serializers.CharField()


class ResendTemporaryCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    type = serializers.ChoiceField(choices=RESEND_CODE_CHOICES)


class SendCodeToNewNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer(many=False)

    class Meta:
        model = User
        fields = ('id', 'avatar', 'full_name', 'username',
                  'date_of_birth', 'email', 'gender', 'phone_number')


class ProfileUpdateSerializer(serializers.ModelSerializer):
    avatar_id = serializers.IntegerField()

    class Meta:
        model = User
        fields = ('avatar_id', 'full_name', 'username',
                  'date_of_birth', 'email', 'gender')
        extra_kwargs = {
            'email': {'validators': []},
        }


class ProfileBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'full_name')


class ProfileBriefWithPhotoSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer()

    class Meta:
        model = User
        fields = ('id', 'full_name', 'avatar')


class EmployeeSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer(many=False)

    class Meta:
        model = User
        fields = ('id', 'avatar', 'full_name', 'phone_number')


class EmployeeWithRoleSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer()
    role = serializers.SerializerMethodField()

    def get_role(self, user: User) -> str:
        return OrganizationService.get_user_role_in_organization(organization=self.context['organization'], user=user)

    class Meta:
        model = User
        fields = ('id', 'avatar', 'full_name', 'role',)


class AttendanceEmployeeSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer()
    role = serializers.SerializerMethodField()
    attendance = serializers.SerializerMethodField()

    def get_role(self, user: User) -> str:
        return OrganizationService.get_user_role_in_organization(organization=self.context['organization'], user=user)

    def get_attendance(self, user: User):
        latest = AttendanceService.get_latest_attendance(employee=user, organization=self.context['organization'])
        if latest is None:
            return None
        from organizations.serializers.attendance_serializers import MembershipListAttendanceSerializer
        return MembershipListAttendanceSerializer(latest).data

    def get_is_arriving(self, user: User) -> bool:
        return not AttendanceService.is_checked_in(employee=user, organization=self.context['organization'])

    class Meta:
        model = User
        fields = ('id', 'avatar', 'full_name', 'role', 'attendance',)


class GlobalAttendanceEmployeeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    attendance = serializers.SerializerMethodField()

    def get_role(self, obj) -> str:
        return OrganizationService.get_user_role_in_organization(organization=obj,
                                                                 user=self.context['user'])

    def get_attendance(self, obj):
        latest = AttendanceService.get_latest_attendance(employee=self.context['user'],
                                                         organization=obj)
        if latest is None:
            return None
        from organizations.serializers.attendance_serializers import MembershipListAttendanceSerializer
        return MembershipListAttendanceSerializer(latest).data

    def get_is_arriving(self, obj) -> bool:
        return not AttendanceService.is_checked_in(employee=self.context['user'], organization=obj)

    class Meta:
        model = Organization
        fields = ('id', 'role', 'attendance')


class GlobalUserAttendanceSerializer(serializers.Serializer):
    organizations = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        fields = ('organizations', 'user')

    def get_organizations(self, _):
        return GlobalAttendanceEmployeeSerializer(self.context['organizations'], context={'user': self.context['user']},
                                                  many=True).data

    def get_user(self, _):
        return UserShortInfoSerializer(self.context['user'], context={'request': self.context['request']}).data


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()


class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class ForgotPasswordSerializer(serializers.Serializer):
    #    type = serializers.ChoiceField(choices=FORGOT_PASSWORD_CHOICES)
    #    email = serializers.CharField(allow_null=True)
    phone_number = serializers.CharField()


class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ('id', 'phone_number')


class PhoneNumberEditSerializer(serializers.Serializer):
    phone_numbers = serializers.ListSerializer(child=serializers.CharField())


class SocialNetworkContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialNetworkContact
        fields = ('id', 'url')


class SocialNetworkEditSerializer(serializers.Serializer):
    networks = serializers.ListSerializer(child=serializers.CharField())


class ChangeAndValidateNewNumberSerializer(serializers.Serializer):
    old_phone_number = serializers.CharField()
    new_phone_number = serializers.CharField()
    code = serializers.IntegerField()


class UserShortInfoSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer()

    class Meta:
        model = User
        fields = ('id', 'full_name', 'avatar', 'username')
