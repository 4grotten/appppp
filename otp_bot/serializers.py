"""DRF Serializers for OTP Bot API."""

import re

from rest_framework import serializers


# --- Request Serializers ---

class SendOTPSerializer(serializers.Serializer):
    """Request for sending OTP."""

    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value: str) -> str:
        value = value.strip()
        if not re.match(r"^\+[1-9]\d{6,14}$", value):
            raise serializers.ValidationError(
                "Invalid phone number. Use E.164 format: +79991234567"
            )
        return value


class VerifyOTPSerializer(serializers.Serializer):
    """Request for verifying OTP. Includes optional registration fields."""

    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(min_length=6, max_length=6)

    # Optional registration fields (required for new users)
    username = serializers.CharField(max_length=255, required=False)
    password = serializers.CharField(min_length=6, max_length=128, required=False)

    def validate_phone_number(self, value: str) -> str:
        value = value.strip()
        if not re.match(r"^\+[1-9]\d{6,14}$", value):
            raise serializers.ValidationError(
                "Invalid phone number. Use E.164 format: +79991234567"
            )
        return value

    def validate_code(self, value: str) -> str:
        if not value.isdigit():
            raise serializers.ValidationError("Code must be 6 digits")
        return value


# --- Response Serializers ---

class OTPBotStatusSerializer(serializers.Serializer):
    """Response for bot status."""

    is_initialized = serializers.BooleanField()
    status = serializers.CharField()
    phone_number = serializers.CharField(allow_null=True)
    session_name = serializers.CharField()


class SendOTPResponseSerializer(serializers.Serializer):
    """Response after sending OTP."""

    otp_id = serializers.CharField()
    phone_number = serializers.CharField()
    expires_at = serializers.CharField()
    sent = serializers.BooleanField()


class VerifyOTPResponseSerializer(serializers.Serializer):
    """Response after verifying OTP."""

    is_valid = serializers.BooleanField()
    error = serializers.CharField(allow_null=True, required=False)


class ErrorSerializer(serializers.Serializer):
    """Generic error response."""

    error = serializers.CharField()
    detail = serializers.CharField(required=False)
