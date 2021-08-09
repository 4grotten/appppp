from django.db import models


class OrganizationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class ActiveOrganizationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(is_deleted=True, is_active=False, is_banned=True)
