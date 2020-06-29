from django.contrib.auth import get_user_model
from rest_framework import serializers

from common.serializers import FileSerializer

User = get_user_model()


class RegisterAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class TemporaryCodeSerializer(serializers.Serializer):
    code = serializers.CharField()
    phone_number = serializers.CharField()


class ResendTemporaryCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class ProfileSerializer(serializers.ModelSerializer):
    avatar = FileSerializer(many=False)

    class Meta:
        model = User
        fields = ('id', 'avatar', 'full_name', 'username',
                  'date_of_birth', 'email', 'gender')


class ProfileUpdateSerializer(serializers.ModelSerializer):
    avatar_id = serializers.IntegerField()

    class Meta:
        model = User
        fields = ('avatar_id', 'full_name', 'username',
                  'date_of_birth', 'email', 'gender')


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField()
