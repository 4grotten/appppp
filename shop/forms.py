from django import forms

from .models import ItemSubcategory


class ItemSubcategoryAdminForm(forms.ModelForm):
    csv_field = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 150, "rows": 15}),
        required=False
    )

    class Meta:
        model = ItemSubcategory
        fields = (
            "id",
            "category",
            "name",
            "name_ru",
            "name_en",
            "name_tr",
            "name_de",
            "name_zh",
            "organization",
            "csv_field",
            "criteria_subcategory",
        )

    def save(self, commit=True):
        instance = super(ItemSubcategoryAdminForm, self).save(commit=False)
        csv_data = self.cleaned_data.get("csv_field")
        category_id = self.cleaned_data.get("category").id
        if csv_data:
            splited_data = csv_data.splitlines()
            for line in splited_data:
                (category_ru, category_en, category_tr, category_de, category_zh) = line.split(";")
                _, _ = ItemSubcategory.objects.update_or_create(
                    category_id=category_id,
                    name_ru=category_ru,
                    name_en=category_en,
                    name_tr=category_tr,
                    name_de=category_de,
                    name_zh=category_zh
                )

        if commit:
            instance.save()
        return instance
