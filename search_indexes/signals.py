from django.db.models.signals import post_save, post_delete
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

    if app_label == 'shop':
        if model_name == 'comment':
            registry.update(instance.item)

    if app_label == 'shop':
        if model_name == 'itemlike':
            registry.update(instance.item)


    if app_label == 'shop':
        if model_name == 'itembookmark':
            registry.update(instance.item)


@receiver(post_delete)
def delete_document(sender, **kwargs):
    """Update document on deleted records.

    Updates Book document from index if related `books.Publisher`
    (`publisher`), `books.Author` (`authors`), `books.Tag` (`tags`) fields
    have been removed from database.
    """
    app_label = sender._meta.app_label
    model_name = sender._meta.model_name
    instance = kwargs['instance']

    if app_label == 'shop':
        if model_name == 'comment':
            registry.update(instance.item)

    if app_label == 'shop':
        if model_name == 'itemlike':
            registry.update(instance.item)
            registry.delete(instance)

    if app_label == 'shop':
        if model_name == 'itembookmark':
            registry.update(instance.item)
            registry.delete(instance)

