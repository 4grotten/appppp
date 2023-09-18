from transactions.models import Transaction
REQUEST_ONLINE_RENTAL_TYPE = 'request_online_rental'
DECLINED_ONLINE_RENTAL_TYPE = 'decline_online_rental'

REQUEST_ONLINE_PAYMENT_TYPE = 'request_online_payment'
ACCEPTED_ONLINE_PAYMENT_TYPE = 'accept_online_payment'
DECLINED_ONLINE_PAYMENT_TYPE = 'decline_online_payment'

ACCEPTED_RENTAL_OFFLINE_PAYMENT_TYPE = 'accept_rental_offline_payment'
DECLINED_RENTAL_OFFLINE_PAYMENT_TYPE = 'decline_rental_offline_payment'

RENTAL_ICON_MAP = {
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS): REQUEST_ONLINE_RENTAL_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS): REQUEST_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS): DECLINED_ONLINE_RENTAL_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED): ACCEPTED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.REJECTED): DECLINED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.REFUNDED): DECLINED_ONLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS): REQUEST_ONLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.ACCEPTED, Transaction.ACCEPTED): ACCEPTED_RENTAL_OFFLINE_PAYMENT_TYPE,
}

REQUEST_ONLINE_TICKET_TYPE = 'request_online_ticket'
ACCEPTED_ONLINE_TICKET_TYPE = 'accept_online_ticket'
DECLINED_ONLINE_TICKET_TYPE = 'decline_online_ticket'

ACCEPTED_TICKET_OFFLINE_PAYMENT_TYPE = 'accept_ticket_offline_payment'
DECLINED_TICKET_OFFLINE_PAYMENT_TYPE = 'decline_ticket_offline_payment'

TICKET_ICON_MAP = {
    # online_payment
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS, Transaction.ONLINE_PAYMENT):
        REQUEST_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS, Transaction.ONLINE_PAYMENT):
        DECLINED_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS, Transaction.ONLINE_PAYMENT):
        REQUEST_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED, Transaction.ONLINE_PAYMENT):
        ACCEPTED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.REJECTED, Transaction.ONLINE_PAYMENT):
        DECLINED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.REFUNDED, Transaction.ONLINE_PAYMENT):
        DECLINED_ONLINE_PAYMENT_TYPE,

    # cash_courier
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS, Transaction.CASH_COURIER):
        REQUEST_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED, Transaction.CASH_COURIER):
        ACCEPTED_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS, Transaction.CASH_COURIER):
        ACCEPTED_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS, Transaction.CASH_COURIER):
        DECLINED_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.ACCEPTED, Transaction.CASH_COURIER):
        DECLINED_ONLINE_TICKET_TYPE,

    # self_pickup
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS, Transaction.SELF_PICKUP):
        REQUEST_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED, Transaction.SELF_PICKUP):
        ACCEPTED_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS, Transaction.SELF_PICKUP):
        ACCEPTED_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS, Transaction.SELF_PICKUP):
        DECLINED_ONLINE_TICKET_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.ACCEPTED, Transaction.SELF_PICKUP):
        DECLINED_ONLINE_TICKET_TYPE,

    # cart_checkout
    (Transaction.OFFLINE, Transaction.ACCEPTED, Transaction.ACCEPTED, Transaction.CART_CHECKOUT):
        ACCEPTED_TICKET_OFFLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS, Transaction.CART_CHECKOUT):
        ACCEPTED_TICKET_OFFLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.REJECTED, Transaction.ACCEPTED, Transaction.CART_CHECKOUT):
        DECLINED_TICKET_OFFLINE_PAYMENT_TYPE,
}


REQUEST_ONLINE_PRODUCT_TYPE = 'request_online_product' # (Онлайн, запрос, запрос, online_payment) и (онлайн, запрос, запрос, cash_courier) и (онлайн, запрос, запрос, self_pickup)
ACCEPTED_ONLINE_PRODUCT_TYPE = 'accept_online_product'
DECLINED_ONLINE_PRODUCT_TYPE = 'decline_online_product'

ACCEPTED_PRODUCT_OFFLINE_PAYMENT_TYPE = 'accept_product_offline_payment' # (офлайн, принят, принят, cart_checkout)
DECLINED_PRODUCT_OFFLINE_PAYMENT_TYPE = 'decline_product_offline_payment'

PRODUCT_ICON_MAP = {
    # online_payment
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS, Transaction.ONLINE_PAYMENT):
        REQUEST_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS, Transaction.ONLINE_PAYMENT):
        DECLINED_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS, Transaction.ONLINE_PAYMENT):
        REQUEST_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED, Transaction.ONLINE_PAYMENT):
        ACCEPTED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.REJECTED, Transaction.ONLINE_PAYMENT):
        DECLINED_ONLINE_PAYMENT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.REFUNDED, Transaction.ONLINE_PAYMENT):
        DECLINED_ONLINE_PAYMENT_TYPE,

    # cash_courier
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS, Transaction.CASH_COURIER):
        REQUEST_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED, Transaction.CASH_COURIER):
        ACCEPTED_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS, Transaction.CASH_COURIER):
        ACCEPTED_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS, Transaction.CASH_COURIER):
        DECLINED_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.ACCEPTED, Transaction.CASH_COURIER):
        DECLINED_ONLINE_PRODUCT_TYPE,

    # self_pickup
    (Transaction.ONLINE, Transaction.IN_PROGRESS, Transaction.IN_PROGRESS, Transaction.SELF_PICKUP):
        REQUEST_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.ACCEPTED, Transaction.SELF_PICKUP):
        ACCEPTED_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS, Transaction.SELF_PICKUP):
        ACCEPTED_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.IN_PROGRESS, Transaction.SELF_PICKUP):
        DECLINED_ONLINE_PRODUCT_TYPE,
    (Transaction.ONLINE, Transaction.REJECTED, Transaction.ACCEPTED, Transaction.SELF_PICKUP):
        DECLINED_ONLINE_PRODUCT_TYPE,

    # cart_checkout
    (Transaction.OFFLINE, Transaction.ACCEPTED, Transaction.ACCEPTED, Transaction.CART_CHECKOUT):
        ACCEPTED_PRODUCT_OFFLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.ACCEPTED, Transaction.IN_PROGRESS, Transaction.CART_CHECKOUT):
        ACCEPTED_PRODUCT_OFFLINE_PAYMENT_TYPE,
    (Transaction.OFFLINE, Transaction.REJECTED, Transaction.ACCEPTED, Transaction.CART_CHECKOUT):
        DECLINED_PRODUCT_OFFLINE_PAYMENT_TYPE,
}