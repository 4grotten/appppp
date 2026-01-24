"""Custom permissions for OTP Bot API."""

from django.conf import settings
from rest_framework.permissions import BasePermission


class IsOTPAdmin(BasePermission):
    """Check X-OTP-API-Key header for admin endpoints."""

    def has_permission(self, request, view) -> bool:
        api_key = request.headers.get("X-OTP-API-Key", "")
        expected_key = getattr(settings, "OTP_ADMIN_API_KEY", "")
        if not expected_key:
            return False
        return api_key == expected_key
