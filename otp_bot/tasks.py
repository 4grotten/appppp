"""Celery tasks for OTP Bot service."""

import logging

from celery import shared_task
from django.utils import timezone

from .models import OTPCode

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_otp_codes():
    """Delete expired OTP codes from database.

    Run periodically via Celery Beat (e.g., every hour).
    """
    count, _ = OTPCode.objects.filter(
        expires_at__lt=timezone.now()
    ).delete()
    if count:
        logger.info(f"[OTP_CLEANUP] Deleted {count} expired OTP codes")
    return {"deleted": count}
