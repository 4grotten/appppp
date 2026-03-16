import logging

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db.utils import OperationalError, ProgrammingError
from storages.backends.s3boto3 import S3Boto3Storage

logger = logging.getLogger(__name__)


def _mask_key(raw_key):
    if not raw_key:
        return "not-set"
    key = str(raw_key)
    if len(key) <= 8:
        return f"{key[:2]}***{key[-2:]}"
    return f"{key[:4]}***{key[-4:]}"


class AdminPriorityS3Storage(S3Boto3Storage):
    """Use active AWSConfig credentials from DB first, fallback to env settings."""

    def __init__(self, *args, **kwargs):
        access_key = getattr(settings, "AWS_ACCESS_KEY_ID", None)
        secret_key = getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
        source = "env_only"
        config_id = None

        if apps.ready:
            try:
                aws_config_model = apps.get_model("api_keys", "AWSConfig")
                active_config = aws_config_model.objects.filter(is_active=True).first()

                if active_config:
                    config_id = active_config.id
                    if not active_config.access_key_id or not active_config.secret_access_key:
                        raise ImproperlyConfigured(
                            "Active AWSConfig must contain both access_key_id and secret_access_key"
                        )
                    access_key = active_config.access_key_id
                    secret_key = active_config.secret_access_key
                    source = "db_active"
            except (OperationalError, ProgrammingError):
                logger.warning(
                    "[AWS_STORAGE] AWSConfig table is unavailable, fallback to env credentials"
                )
            except LookupError:
                logger.warning(
                    "[AWS_STORAGE] AWSConfig model not found, fallback to env credentials"
                )

        kwargs.setdefault("access_key", access_key)
        kwargs.setdefault("secret_key", secret_key)
        kwargs.setdefault("bucket_name", getattr(settings, "AWS_STORAGE_BUCKET_NAME", None))
        kwargs.setdefault("region_name", getattr(settings, "AWS_S3_REGION_NAME", None))

        super().__init__(*args, **kwargs)

        logger.info(
            "[AWS_STORAGE] source=%s config_id=%s access_key_id=%s bucket=%s region=%s",
            source,
            config_id,
            _mask_key(access_key),
            getattr(settings, "AWS_STORAGE_BUCKET_NAME", None),
            getattr(settings, "AWS_S3_REGION_NAME", None),
        )
