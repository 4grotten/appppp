from django.contrib.auth import get_user_model
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from common.serializers import ImageSerializer
from organizations.models import Organization
from organizations.services.attendance_services import AttendanceService
from organizations.services.organization_promo_services import PromoSubscriberService
from organizations.services.organization_services import OrganizationService
from organizations.services.subscription_services import SubscriptionService
from .constants import RESEND_CODE_CHOICES
from .models import PhoneNumber, SocialNetworkContact, MyOwnToken

User = get_user_model()


class RegisterAuthSerializer(serializers.Serializer):
    phone_number = PhoneNumberField()
    location = serializers.CharField(allow_null=True, required=False)
    device = serializers.CharField(allow_null=True, required=False)
    version_app = serializers.CharField(allow_null=True, required=False)


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(allow_null=True)


class TemporaryCodeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    phone_number = serializers.CharField()
    location = serializers.CharField(allow_null=True, required=False)
    device = serializers.CharField(allow_null=True, required=False)
    version_app = serializers.CharField(allow_null=True, required=False)


class ResendTemporaryCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    type = serializers.ChoiceField(choices=RESEND_CODE_CHOICES)


class SendCodeToNewNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer(many=False)
    has_empty_fields = serializers.SerializerMethodField()

    def get_has_empty_fields(self, user: User):
        empty = {None, ''}
        fields = set(list(User.objects.filter(id=user.id).values_list('email', 'date_of_birth', 'username'))[0])
        if empty & fields:
            return True
        return False

    class Meta:
        model = User
        fields = ('id', 'avatar', 'full_name', 'username',
                  'date_of_birth', 'email', 'gender', 'phone_number', 'has_empty_fields',)


class ProfileUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)
    avatar_id = serializers.IntegerField(required=False, allow_null=True)
    device_type = serializers.CharField(required=False, default=None, allow_null=True, allow_blank=True)

    class Meta:
        model = User
        fields = ('avatar_id', 'full_name', 'username',
                  'date_of_birth', 'email', 'gender', 'device_type')


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
    image = ImageSerializer()

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
        fields = ('id', 'role', 'attendance', 'title', 'image')


class GlobalUserAttendanceSerializer(serializers.Serializer):
    organizations = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        fields = ('organizations', 'user')

    def get_organizations(self, _):
        return GlobalAttendanceEmployeeSerializer(self.context['organizations'], context={
            'user': self.context['user'],
            'request': self.context['request']
        }, many=True).data

    def get_user(self, _):
        return UserShortInfoSerializer(self.context['user'], context={'request': self.context['request']}).data


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8)


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()
    location = serializers.CharField(allow_null=True, required=False)
    device = serializers.CharField(allow_null=True, required=False)
    version_app = serializers.CharField(allow_null=True, required=False)
    operating_system = serializers.CharField(allow_null=True, required=False)


class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)


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


class FollowerListSerializer(UserShortInfoSerializer):
    has_promo_cashback = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'full_name', 'has_promo_cashback', 'avatar', 'is_subscribed')

    def get_has_promo_cashback(self, user: User) -> bool:
        if not self.context['can_edit']:
            return False
        return PromoSubscriberService.user_has_promo_cashback(user=user, organization=self.context['organization'])

    def get_is_subscribed(self, user: User) -> str:
        if not self.context['can_edit']:
            return 'subscribed'
        return SubscriptionService.is_subscribed(organization=self.context['organization'], user=user)


class FollowerOrClientSerializer(FollowerListSerializer):
    role = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'full_name', 'has_promo_cashback', 'avatar', 'phone_number', 'role', 'is_subscribed')

    def get_has_promo_cashback(self, user: User) -> bool:
        organization = OrganizationService.get(id=self.context['organization_id'])
        return PromoSubscriberService.user_has_promo_cashback(user=user, organization=organization)

    def get_role(self, user: User) -> str:
        return OrganizationService.get_user_role_in_organization_or_client(
            organization_id=self.context['organization_id'], user=user)

    def get_is_subscribed(self, user: User) -> str:
        organization = OrganizationService.get(id=self.context['organization_id'])
        return SubscriptionService.is_subscribed(organization=organization, user=user)


class UserWhitClientOrRoleInfoSerializer(serializers.ModelSerializer):
    avatar = ImageSerializer()
    role = serializers.SerializerMethodField()

    def get_role(self, user: User) -> str:
        return OrganizationService.get_user_role_in_organization_or_client(
            organization_id=self.context['organization'].id, user=user)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'avatar', 'role')


class MyOwnTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyOwnToken
        fields = ('id', 'key', 'user', 'location', 'device', 'ip', 'log_time', 'version_app','is_active',
                  'operating_system', 'user_agent')
