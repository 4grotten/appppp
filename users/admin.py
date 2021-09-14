from io import BytesIO

import pandas as pd
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.http import HttpResponse
from django.urls import reverse, path
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import TokenProxy

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
        'get_user_organizations_link'
    )
    list_filter = ('gender', 'is_active', 'is_staff', 'is_superuser',)
    search_fields = ('phone_number', 'full_name',)
    raw_id_fields = ('avatar',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'email', 'gender', 'phone_number', 'full_name', 'avatar', 'date_of_birth',
            'is_new_user')}),
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

    def get_urls(self):
        return [
                   path(
                       '<id>/user_organizations/',
                       self.admin_site.admin_view(self.get_user_organizations),
                       name='user_organizations',
                   ),
               ] + super().get_urls()

    def lookup_allowed(self, lookup, value):
        # Don't allow lookups involving passwords.
        return not lookup.startswith('user_organizations') and super().lookup_allowed(lookup, value)

    def get_user_organizations(self, request, **kwargs):
        """
        Название организации
        Вид деятельности
        номер телефона
        номер телефона
        instagram
        страна
        город
        адрес
        """
        target_user_id = kwargs['id']
        target_user = User.objects.get(pk=target_user_id)
        organizations = target_user.owned_organizations.all().order_by('-created_at')
        titles = []
        types = []
        phone_numbers_1 = []
        phone_numbers_2 = []
        instagrams = []
        countries = []
        cities = []
        addresses = []
        for organization in organizations:
            titles.append(organization.title)
            types.append(organization.types.first().title_ru)
            try:
                phone_numbers_1.append((organization.phone_numbers.first()))
            except:
                phone_numbers_1.append("")
            try:
                phone_numbers_2.append((organization.phone_numbers.all[2]))
            except:
                phone_numbers_2.append("")
            try:
                instagrams.append(organization.instagram_integration_link.first().url)
            except:
                instagrams.append("")

            try:
                cities.append(organization.city.name_ru)
            except:
                cities.append("")
            countries.append(organization.country.name_ru)
            addresses.append(organization.address)


        dict_data = {
            _('Название организации'): titles,
            _('Вид деятельности'): types,
            _("номер телефона1"): phone_numbers_1,
            _("номер телефона2"): phone_numbers_2,
            _("instagram"): instagrams,
            _("страна"): countries,
            _("город"): cities,
            _("адрес"): addresses
        }
        df = pd.DataFrame(dict_data)
        with BytesIO() as b:
            # Use the StringIO object as the filehandle.
            writer = pd.ExcelWriter(b, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Sheet1', index=False)
            writer.save()
            # Set up the Http response.
            filename = '{username}_organizations.xlsx'.format(username=target_user.phone_number)
            response = HttpResponse(
                b.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            return response

    def get_user_organizations_link(self, obj):
        url = reverse('admin:user_organizations', args=[obj.id])
        name = _("Download user organizations")
        return mark_safe(
            "<a href='{url}' class='button'>{name}</a>".format(
                url=url, name=name
            )
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
    search_fields = ('user__phone_number','user__username','user__full_name' )
    raw_id_fields = ('user',)


admin.site.register(TokenProxy, ApofizTokenAdmin)
