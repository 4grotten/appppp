from django.contrib import admin

from common.models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    pass
