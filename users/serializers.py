from rest_framework import serializers


class RegisterAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField()


class TemporaryCodeSerializer(serializers.Serializer):
    code = serializers.CharField()
    phone_number = serializers.CharField()
