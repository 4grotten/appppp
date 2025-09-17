from django import forms
from django.contrib import admin
from common.models import Country


class CountryAdminForm(forms.ModelForm):
    class Meta:
        model = Country
        fields = "__all__"
        widgets = {
            "flag": forms.TextInput(attrs={"size": 80}),
        }
