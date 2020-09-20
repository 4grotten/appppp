from django.db import transaction

from organizations.models import Organization, CashbackGroup


class CashbackGroupService:
    @classmethod
    def get_partners_in_same_cashback_group(cls, organization: Organization) -> list:
        group = organization.cashback_group

        if group is None:
            return []

        return list(group.organizations.exclude(id=organization.id).values_list('id', flat=True))

    @classmethod
    @transaction.atomic
    def link_organizations_in_cashback_group(cls, first: Organization, second: Organization):
        # Do not update groups if organizations already have cashback groups
        if first.cashback_group is not None and second.cashback_group is not None:
            return

        if first.cashback_group is None and second.cashback_group is None:
            new_group = CashbackGroup.objects.create(name=f'Group initiated by {first.title} and {second.title}')
            first.cashback_group = new_group
            second.cashback_group = new_group
            first.save(update_fields=('cashback_group',))
            second.save(update_fields=('cashback_group',))
            return

        if first.cashback_group is None:
            first.cashback_group = second.cashback_group
            first.save(update_fields=('cashback_group',))
        else:
            second.cashback_group = first.cashback_group
            second.save(update_fields=('cashback_group',))
