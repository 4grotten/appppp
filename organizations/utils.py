import boto3
from django.conf import settings


class JSONQuerySet(list):

    def filter(self, **kwargs):
        result = self
        for key, value in kwargs.items():
            result = [obj for obj in result if obj.get(key) == value]

        return JSONQuerySet(result)


def create_download_url(file_key):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
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
