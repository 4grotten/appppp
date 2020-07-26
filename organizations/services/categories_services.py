from django.db.models import QuerySet, Count

from organizations.models import OrganizationCategory, Organization


class OrganizationCategoryService:
    @classmethod
    def get_nonempty_categories(cls, partner: Organization = None) -> QuerySet:
        # ToDo: Exclude categories where all organizations are deactivated (Rare case)
        if partner is None:
            return OrganizationCategory.objects.filter(types__organizations__isnull=False).annotate(
                orgs_count=Count('types__organizations', distinct=True)).distinct().order_by('-orgs_count')

        return OrganizationCategory.objects.filter(
            types__organizations__in=partner.requested_partnerships.filter(is_accepted=True).values_list(
                'accepted_by', flat=True)).annotate(
            orgs_count=Count('types__organizations', distinct=True)).distinct().order_by('-orgs_count')
