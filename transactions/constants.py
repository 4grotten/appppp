from transactions.models import Transaction
REQUEST_ONLINE_RENTAL_TYPE = 'request_online_rental'
DECLINED_ONLINE_RENTAL_TYPE = 'decline_online_rental'

REQUEST_ONLINE_PAYMENT_TYPE = 'request_online_payment'
ACCEPTED_ONLINE_PAYMENT_TYPE = 'accept_online_payment'
DECLINED_ONLINE_PAYMENT_TYPE = 'decline_online_payment'

ACCEPTED_OFFLINE_PAYMENT_TYPE = 'accept_offline_payment'
DECLINED_OFFLINE_PAYMENT_TYPE = 'decline_offline_payment'

ICON_MAP = {
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS): REQUEST_ONLINE_RENTAL_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS): REQUEST_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS): DECLINED_ONLINE_RENTAL_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED): ACCEPTED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.REJECTED): DECLINED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.REFUNDED): DECLINED_ONLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS): REQUEST_ONLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.ACCEPTED, Transaction.ACCEPTED): ACCEPTED_OFFLINE_PAYMENT_TYPE,
}

REQUEST_ONLINE_TICKET_TYPE = 'request_online_ticket'
DECLINED_ONLINE_TICKET_TYPE = 'decline_online_ticket'

ACCEPTED_TICKET_OFFLINE_PAYMENT_TYPE = 'accept_ticket_offline_payment'
DECLINED_TICKET_OFFLINE_PAYMENT_TYPE = 'decline_ticket_offline_payment'

TICKET_ICON_MAP = {
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS): REQUEST_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS): REQUEST_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS): DECLINED_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED): ACCEPTED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.REJECTED): DECLINED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.REFUNDED): DECLINED_ONLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS): REQUEST_ONLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.ACCEPTED, Transaction.ACCEPTED): ACCEPTED_TICKET_OFFLINE_PAYMENT_TYPE,
}