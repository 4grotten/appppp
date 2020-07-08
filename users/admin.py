from django.contrib import admin
from django.contrib.auth import get_user_model

from users.models import TemporaryCode, PhoneNumber, SocialNetworkContact, TemporaryPhoneNumber

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(TemporaryCode)
class TemporaryCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'is_used', 'expiration_datetime',)


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    pass


@admin.register(SocialNetworkContact)
class SocialNetworkContactAdmin(admin.ModelAdmin):
    pass


@admin.register(TemporaryPhoneNumber)
class TemporaryPhoneNumberAdmin(admin.ModelAdmin):
    pass
