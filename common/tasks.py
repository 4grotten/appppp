import time
import logging
from celery import shared_task
from django.core.files.storage import default_storage
from imagekit.cachefiles import ImageCacheFile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_image_versions(file_path, spec_id):
    logger.info(f"Starting image generation for {file_path} with spec {spec_id}")

    try:
        with default_storage.open(file_path, "rb") as file_obj:
            cache_file = ImageCacheFile(spec_id=spec_id, source=file_obj)
            cache_file.generate()
            logger.info(
                f"Successfully generated image for {file_path} with spec {spec_id}"
            )
    except Exception as e:
        logger.error(
            f"Error generating image for {file_path} with spec {spec_id}: {str(e)}"
        )
        raise
