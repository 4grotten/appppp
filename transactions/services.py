from common.exceptions import NotAcceptableException
from organizations.models import Organization
from organizations.services import OrganizationService
from transactions.models import Transaction
from users.models import User


class TransactionService:
    @classmethod
    def preprocess_transaction(cls, client: User, organization: Organization, processed_by: User) -> Transaction:
        if not OrganizationService.user_can_sell(organization=organization, user=processed_by):
            raise NotAcceptableException('No rights to sell in this organization')

        transaction = Transaction.objects.create(client=client, organization=organization, processed_by=processed_by)
        return transaction
