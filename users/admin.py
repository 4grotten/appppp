from django.contrib import admin
from django.contrib.auth import get_user_model

from users.models import TemporaryCode, PhoneNumber, SocialNetworkContact, TemporaryPhoneNumber

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'full_name', 'username', 'gender', 'avatar')
    list_filter = ('gender',)
    search_fields = ('phone_number', 'full_name',)
    raw_id_fields = ('avatar',)


@admin.register(TemporaryCode)
class TemporaryCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'is_used', 'expiration_datetime',)


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number')


@admin.register(SocialNetworkContact)
class SocialNetworkContactAdmin(admin.ModelAdmin):
    list_display = ('user', 'url')


@admin.register(TemporaryPhoneNumber)
class TemporaryPhoneNumberAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'code')
