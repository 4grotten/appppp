from django.db import transaction

from organizations.models import Organization, CumulativeGroup


class CumulativeGroupService:
    @classmethod
    def get_partners_in_same_cumulative_group(cls, organization: Organization) -> list:
        group = organization.cumulative_group
        if group is None:
            return []

        return list(group.organizations.exclude(id=organization.id).values_list('id', flat=True))

    @classmethod
    @transaction.atomic
    def link_organizations_in_cumulative_group(cls, first: Organization, second: Organization):
        # Do not update groups if organizations already have cumulative groups
        if first.cumulative_group is not None and second.cumulative_group is not None:
            return

        if first.cumulative_group is None and second.cumulative_group is None:
            new_group = CumulativeGroup.objects.create(name=f'Group initiated by {first.title} and {second.title}')
            first.cumulative_group = new_group
            second.cumulative_group = new_group
            first.save(update_fields=('cumulative_group',))
            second.save(update_fields=('cumulative_group',))
            return

        if first.cumulative_group is None:
            first.cumulative_group = second.cumulative_group
            first.save(update_fields=('cumulative_group',))
        else:
            second.cumulative_group = first.cumulative_group
            second.save(update_fields=('cumulative_group',))
