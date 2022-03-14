from django.contrib import admin

from sms_sender.models import SmsModel


@admin.register(SmsModel)
class SmsModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'phone_number', 'text', 'status')

