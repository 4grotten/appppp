# from django.contrib.admin.models import LogEntry
# from django.db.models.signals import post_save, post_delete
# from django.dispatch import receiver
#
# from django_elasticsearch_dsl.registries import registry
#
# from search_indexes.tasks import update_indexes, delete_indexes
#
#
# @receiver(post_save)
# def update_document(sender, **kwargs):
#     """Update document on added/changed records."""
#
#     app_label = sender._meta.app_label
#     model_name = sender._meta.model_name
#     instance = kwargs['instance']
#     print(kwargs['instance'], 'kwargs_instance!!!')
#     print(app_label, 'app_label')
#     print(instance.id)
#
#     # if isinstance(instance, LogEntry):
#     #     if instance.content_type.model == 'organization':
#     #         print(type(instance.object_id), 'asd!!!')
#     #         instances = Organization.objects.get(id=instance.object_id).shop_items.all()
#     #         for _instance in instances:
#     #             print(_instance, 'update_instances!!!')
#     #             registry.update(_instance)
#             # print(instancee, 'org!!!')
#             # print(instance.content_type.model == 'organization')
#             # print(instance.object_id, 'instance.object_id!!!')
#             # print(instance.object_repr, 'instance.object_repr!!!')
#             # print(instance.action_flag, 'instance.action_flag!!!')
#
#     if app_label == 'organizations':
#         if model_name == 'organization':
#
#             update_indexes.delay(organization_id=instance.id)
#             # print(instances)
#             # for _instance in instances:
#             #     print(_instance, 'update_document!!!')
#             #     registry.update(_instance)
#
#     if app_label == 'shop':
#         if model_name == 'shopitem':
#             registry.update(instance)
#
#
# @receiver(post_delete)
# def delete_document(sender, **kwargs):
#     """Update document on deleted records."""
#
#     app_label = sender._meta.app_label
#     model_name = sender._meta.model_name
#     instance = kwargs['instance']
#     print(app_label, 'app_label3!!!')
#     print(model_name, 'model_name3!!!')
#     print(instance, 'instance3!!!')
#
#
#     if app_label == 'shop':
#         if model_name == 'shopitem':
#             if instance.is_published is False and instance.organization.is_banned is True:
#                 registry.delete(instance)
#
#     if app_label == 'organizations':
#         if model_name == 'organization':
#             delete_indexes.delay(organization_id=instance.id)
