from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import File
from .tasks import generate_image_versions


@receiver(post_save, sender=File)
def schedule_imagekit_generation(sender, instance: File, created, **kwargs):
    if created and instance.file:
        generate_image_versions.delay(instance.id)
