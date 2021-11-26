from django.db.models.signals import post_save
from django.dispatch import receiver

from django_elasticsearch_dsl.registries import registry


@receiver(post_save)
def update_document(sender, **kwargs):
    """Update document on added/changed records."""

    app_label = sender._meta.app_label
    model_name = sender._meta.model_name
    instance = kwargs['instance']

    if app_label == 'organizations':
        if model_name == 'organization':
            instances = instance.shop_items.all()
            for _instance in instances:
                registry.update(_instance)
