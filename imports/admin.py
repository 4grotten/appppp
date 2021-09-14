from django.contrib import admin

# Register your models here.
from django.contrib.auth import get_user_model

from imports.import_service import import_organization_for_user
from imports.models import OrganizationsImportFile
User = get_user_model()

class OrganizationsImportFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone_number', 'num_rows', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    raw_id_fields = ('user',)

    def save_model(self, request, obj, form, change):
        obj.user = request.user
        # if change:
        #     print(form)
        # print(form)
        try:
            import_user = User.objects.get(phone_number=obj.phone_number)
            import_organization_for_user(import_user, obj.file.url)
        except User.DoesNotExist:
            pass
        super(OrganizationsImportFileAdmin, self).save_model(request, obj, form, change)


admin.site.register(OrganizationsImportFile, OrganizationsImportFileAdmin)
