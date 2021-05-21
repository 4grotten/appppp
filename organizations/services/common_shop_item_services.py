from django.db import transaction

from organizations.models import Organization, CommonItemsGroup


class CommonItemsGroupService:
    @classmethod
    def get_partners_with_common_items(cls, organization: Organization) -> list:
        group = organization.items_group
        if group is None:
            return []

        return list(group.organizations.exclude(id=organization.id).values_list('id', flat=True))

    @classmethod
    @transaction.atomic
    def link_organizations_with_common_items_group(cls, first: Organization, second: Organization):
        # Do not update groups if organizations already have common items groups
        if first.items_group is not None and second.items_group is not None:
            return

        if first.items_group is None and second.items_group is None:
            new_group = CommonItemsGroup.objects.create(
                name=f'Common items group initiated by {first.title} and {second.title}')
            first.items_group = new_group
            second.items_group = new_group
            first.save(update_fields=('items_group',))
            second.save(update_fields=('items_group',))
            return

        if first.items_group is None:
            first.items_group = second.items_group
            first.save(update_fields=('items_group',))
        else:
            second.items_group = first.items_group
            second.save(update_fields=('items_group',))
