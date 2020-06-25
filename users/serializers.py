from rest_framework import serializers


class RegisterAuthSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
