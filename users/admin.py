from django.contrib import admin
from django.contrib.auth import get_user_model

from users.models import TemporaryCode, PhoneNumber, SocialNetworkContact

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(TemporaryCode)
class TemporaryCodeAdmin(admin.ModelAdmin):
    pass


@admin.register(PhoneNumber)
class PhoneNumberAdmin(admin.ModelAdmin):
    pass


@admin.register(SocialNetworkContact)
class SocialNetworkContactAdmin(admin.ModelAdmin):
    pass
