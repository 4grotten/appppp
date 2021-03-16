from django import forms

from .models import ItemSubcategory
from .tasks import upload_item_subcategories


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
            "organization",
            "csv_field"
        )

    def save(self, commit=True):
        instance = super(ItemSubcategoryAdminForm, self).save(commit=False)
        csv_data = self.cleaned_data.get("csv_field")
        category_id = self.cleaned_data.get("category").id
        if csv_data:
            upload_item_subcategories.delay(
                csv_data=csv_data,
                category_id=category_id
            )

        if commit:
            instance.save()
        return instance
