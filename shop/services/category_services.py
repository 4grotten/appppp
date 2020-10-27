from django.db.models import QuerySet, Count, Q

from shop.models import ItemSubcategory


class ItemSubcategoryService:
    @classmethod
    def get_nonempty_subcategories(cls, organization_id: int) -> QuerySet:
        subcategories = ItemSubcategory.objects.filter(
            Q(organization__isnull=True) | Q(organization_id=organization_id))
        return subcategories.annotate(items_count=Count('items_in_category')).filter(items_count__gt=0)
