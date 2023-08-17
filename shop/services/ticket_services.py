from common.exceptions import ObjectNotFoundException, BadRequestException, IntegrityException
from notifications.constants import NOTIFICATION_MODE_TICKET, ACTIVATE_TICKET_CLIENT_TYPE, ACTIVATE_TICKET_TYPE
from shop.models import Ticket
from notifications.tasks import sent_notification

from django.utils.translation import gettext_lazy as _


class TicketService:
    @classmethod
    def get(cls, *args, **kwargs):
        try:
            return Ticket.objects.get(*args, **kwargs)
        except Ticket.DoesNotExist:
            raise ObjectNotFoundException(_('Booking not found'))

    @classmethod
    def activate_ticket(cls, ticket: Ticket):
        ticket = cls.get(id=ticket.id)
        if ticket.is_active:
            raise BadRequestException(message=_('This ticket already was activated'))
        try:
            ticket.is_active = True
            ticket.save()
        except:
            raise IntegrityException()

        transaction = ticket.transaction

        extra_data = {
            'transaction_id': transaction.id,
            'total_price': transaction.final_amount,
            'discount_percent': transaction.discount_percent,
            'currency': transaction.currency.code
        }

        sent_notification.delay(
            recipient_id=transaction.client_id,
            sender_id=transaction.processed_by_id,
            mode=NOTIFICATION_MODE_TICKET,
            notification_type=ACTIVATE_TICKET_CLIENT_TYPE,
            organization_id=transaction.organization_id,
            extra_data=extra_data
        )

        sent_notification.delay(
            recipient_id=transaction.processed_by_id,
            sender_id=transaction.client_id,
            mode=NOTIFICATION_MODE_TICKET,
            notification_type=ACTIVATE_TICKET_TYPE,
            organization_id=transaction.organization_id,
            extra_data=extra_data
        )