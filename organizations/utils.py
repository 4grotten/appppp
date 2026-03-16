import boto3
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from decimal import Decimal
from api_keys.models import AWSConfig


class JSONQuerySet(list):

    def filter(self, **kwargs):
        result = self
        for key, value in kwargs.items():
            result = [obj for obj in result if obj.get(key) == value]

        return JSONQuerySet(result)


def create_download_url(file_key):
    active_aws_config = AWSConfig.objects.filter(is_active=True).first()
    if active_aws_config:
        if not active_aws_config.access_key_id or not active_aws_config.secret_access_key:
            raise ImproperlyConfigured(
                "Active AWSConfig must contain both access_key_id and secret_access_key"
            )
        aws_access_key_id = active_aws_config.access_key_id
        aws_secret_access_key = active_aws_config.secret_access_key
    else:
        aws_access_key_id = settings.AWS_ACCESS_KEY_ID
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY

    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    file_key = str(file_key)
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": settings.AWS_STORAGE_BUCKET_NAME,
            "Key": file_key,
            "ResponseContentDisposition": f'attachment; filename="{file_key.split("/")[-1]}"',
        },
        ExpiresIn=3600,
    )

    return url


def clean_original_amount(value: str) -> Decimal:
    cleaned_value = value.replace(",", "").replace(" ", "")

    return Decimal(cleaned_value)
