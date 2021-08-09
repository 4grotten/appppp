from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField, UsernameField, UserChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.admin import TokenChangeList, TokenAdmin
from rest_framework.authtoken.models import TokenProxy, Token

from users.models import TemporaryCode, PhoneNumber, SocialNetworkContact, TemporaryPhoneNumber

User = get_user_model()

class ApofizUserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = '__all__'
        field_classes = {}



@admin.register(User)
class ApofizUserAdmin(UserAdmin):
    form = ApofizUserChangeForm
    list_display = (
        'phone_number', 'full_name', 'username', 'gender', 'avatar', 'is_active', 'is_staff', 'is_superuser', 'id',
    )
    list_filter = ('gender', 'is_active', 'is_staff', 'is_superuser',)
    search_fields = ('phone_number', 'full_name',)
    raw_id_fields = ('avatar',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'gender', 'phone_number', 'full_name', 'avatar', 'date_of_birth', 'is_new_user')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'password1', 'password2'),
        }),
    )

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

admin.site.unregister(TokenProxy)


class ApofizTokenAdmin(TokenAdmin):
    raw_id_fields = ('user',)

admin.site.register(TokenProxy, ApofizTokenAdmin)