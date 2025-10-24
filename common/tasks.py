import time
from celery import shared_task
from django.core.files.storage import default_storage
from .models import File


@shared_task(bind=True, max_retries=3)
def generate_image_versions(self, file_id):
    try:
        file_instance = File.objects.get(id=file_id)
    except File.DoesNotExist:
        return

    file_name = file_instance.file.name

    max_wait = 30
    waited = 0
    while not default_storage.exists(file_name):
        raise self.retry(
            exc=Exception(f"File {file_name} not found on S3"), countdown=5
        )

    try:
        file_instance.file.open()
        file_instance.large.generate()
        file_instance.medium.generate()
        file_instance.small.generate()
        print(f"[CELERY] ImageKit versions generated for {file_name}")
    except Exception as e:
        raise self.retry(exc=e, countdown=5)
    finally:
        file_instance.file.close()
