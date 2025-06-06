from django import forms

from .models import UserAppType


class UserAppTypeAdminForm(forms.ModelForm):
    csv_field = forms.CharField(
        widget=forms.Textarea(attrs={"cols": 150, "rows": 15}),
        required=False,
        help_text="Формат: title_ru;title_en;title_tr;title_de;title_zh (каждый тип на новой строке)"
    )

    class Meta:
        model = UserAppType
        fields = (
            "id",
            "category",
            "title",
            "title_ru",
            "title_en",
            "title_tr",
            "title_de",
            "title_zh",
            "is_adult",
            "csv_field",
        )

    def save(self, commit=True):
        instance = super(UserAppTypeAdminForm, self).save(commit=False)
        csv_data = self.cleaned_data.get("csv_field")
        category = self.cleaned_data.get("category")

        if csv_data and category:
            splited_data = csv_data.splitlines()
            for line in splited_data:
                line = line.strip()
                if not line:  # пропускаем пустые строки
                    continue

                parts = line.split(";")
                if len(parts) != 5:
                    continue  # пропускаем некорректные строки

                (title_ru, title_en, title_tr, title_de, title_zh) = parts

                _, _ = UserAppType.objects.update_or_create(
                    category=category,
                    title_ru=title_ru.strip(),
                    defaults={
                        'title_en': title_en.strip(),
                        'title_tr': title_tr.strip(),
                        'title_de': title_de.strip(),
                        'title_zh': title_zh.strip(),
                    }
                )

        if commit:
            instance.save()
        return instance