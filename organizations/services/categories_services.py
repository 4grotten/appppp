from django.db.models import QuerySet

from organizations.models import OrganizationCategory


class OrganizationCategoryService:
    @classmethod
    def get_nonempty_categories(cls) -> QuerySet:
        # ToDo: Exclude categories where all organizations are deactivated (Rare case)
        return OrganizationCategory.objects.filter(types__organizations__isnull=False)
