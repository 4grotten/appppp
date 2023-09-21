from decimal import Decimal

from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException
from common.models import File
from transactions.models import Recipient, PayoutSystem, Balance


class RecipientService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Recipient.objects.get(**kwargs)
        except Recipient.DoesNotExist:
            raise ObjectNotFoundException(_('Recipient not found'))

    @classmethod
    def create_recipient(cls, payout_system: PayoutSystem, owner_name_on_card: str, card_number: str,
                         transfer_amount: Decimal, image_id: File = None,):
        try:
            payout_system = PayoutSystem.objects.get(id=payout_system.id)
            recipient = Recipient.objects.create(payout_system=payout_system,
                                                 owner_name_on_card=owner_name_on_card, card_number=card_number,
                                                 transfer_amount=transfer_amount)
            if image_id is not None:
                recipient.image = image_id
                recipient.save()
            else:
                image = payout_system.image
                recipient.image = image
                recipient.save()
        except PayoutSystem.DoesNotExist:
            raise ObjectNotFoundException(_('PayoutSystem not found'))
        return recipient


    @classmethod
    def get_organization_balance_recipient(cls, balance: Balance):

        recipients = Recipient.objects.filter(payout_system__in=balance.payout_systems.all())

        return recipients

