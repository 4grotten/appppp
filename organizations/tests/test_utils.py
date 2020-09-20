from organizations.models import Organization
from organizations.services.cashback_group_services import CashbackGroupService
from organizations.tests.factories import PartnershipFactory


class PartnershipUtils:
    @staticmethod
    def create_partnership_with_shared_cashback(org1: Organization, org2: Organization):
        PartnershipFactory(requested_by=org1, accepted_by=org2, is_accepted=True, can_share_cashback=True)
        PartnershipFactory(requested_by=org2, accepted_by=org1, is_accepted=True, can_share_cashback=True)

        CashbackGroupService.link_organizations_in_cashback_group(first=org1, second=org2)

    @staticmethod
    def create_partnership_with_one_sided_cashback(org1: Organization, org2: Organization):
        PartnershipFactory(requested_by=org1, accepted_by=org2, is_accepted=True, can_share_cashback=True)
        PartnershipFactory(requested_by=org2, accepted_by=org1, is_accepted=True, can_share_cashback=False)
