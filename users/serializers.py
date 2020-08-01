from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.serializers import ImageSerializer
from .constants import RESEND_CODE_CHOICES, REGISTER_AUTH_TYPE
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
