from typing import Union

from django.db.models import QuerySet, Count

from common.models import Country, City
from organizations.models import OrganizationCategory, Organization


class OrganizationCategoryService:
    @classmethod
    def get_nonempty_categories(cls, partner: Organization = None,
                                country: Union[Country, None] = None,
                                city: Union[City, None] = None) -> QuerySet:
        # ToDo: Exclude categories where all organizations are deactivated (Rare case)
        queryset = OrganizationCategory.objects.all()
        if country is not None:
            queryset = queryset.filter(types__organizations__country=country)
        if city is not None:
            queryset = queryset.filter(types__organizations__city=city)

        if partner is None:
            return queryset.filter(types__organizations__isnull=False).annotate(
                orgs_count=Count('types__organizations', distinct=True)).distinct().order_by('-orgs_count')

        return queryset.filter(
            types__organizations__in=partner.requested_partnerships.filter(is_accepted=True).values_list(
                'accepted_by', flat=True)).annotate(
            orgs_count=Count('types__organizations', distinct=True)).distinct().order_by('-orgs_count')

    @classmethod
    def filter(cls, **filters):
        return OrganizationCategory.objects.filter(**filters)
