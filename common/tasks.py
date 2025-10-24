import logging
from io import BytesIO
from celery import shared_task
from django.core.files.storage import default_storage
from imagekit.cachefiles import ImageCacheFile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_image_versions(self, file_path, spec_id):
    logger.info(f"Generating image specs for {file_path} spec: {spec_id}")

    try:
        with default_storage.open(file_path, "rb") as file_obj:
            file_content = file_obj.read()
        file_obj = BytesIO(file_content)

        cache_file = ImageCacheFile(spec_id=spec_id, source=file_obj)
        cache_file.generate()
        logger.info(f"Successfuly created spec {spec_id} for image {file_path}")
    except Exception as e:
        logger.error(f"Error while generating image specs {str(e)}")
        raise self.retry(exc=e)
