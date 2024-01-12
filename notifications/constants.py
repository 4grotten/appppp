NOTIFICATION_MODE_DISCOUNT = 'discount'
NOTIFICATION_MODE_SUBSCRIPTION = 'subscription'
NOTIFICATION_MODE_SYSTEM = 'system'
NOTIFICATION_MODE_PARTNER = 'partner'
NOTIFICATION_MODE_PERSONAL = 'personal'
NOTIFICATION_MODE_PRODUCT = 'product'
NOTIFICATION_MODE_RENTAL = 'rental'
NOTIFICATION_MODE_TICKET = 'ticket'
NOTIFICATION_MODE_RESUME = 'resume'


NOTIFICATION_MODES = (
    (NOTIFICATION_MODE_DISCOUNT, NOTIFICATION_MODE_DISCOUNT.capitalize()),
    (NOTIFICATION_MODE_SUBSCRIPTION, NOTIFICATION_MODE_SUBSCRIPTION.capitalize()),
    (NOTIFICATION_MODE_SYSTEM, NOTIFICATION_MODE_SYSTEM.capitalize()),
    (NOTIFICATION_MODE_PARTNER, NOTIFICATION_MODE_PARTNER.capitalize()),
    (NOTIFICATION_MODE_PERSONAL, NOTIFICATION_MODE_PERSONAL.capitalize()),
    (NOTIFICATION_MODE_PRODUCT, NOTIFICATION_MODE_PRODUCT.capitalize()),
    (NOTIFICATION_MODE_RENTAL, NOTIFICATION_MODE_RENTAL.capitalize()),
    (NOTIFICATION_MODE_TICKET, NOTIFICATION_MODE_TICKET.capitalize()),
    (NOTIFICATION_MODE_RESUME, NOTIFICATION_MODE_RESUME.capitalize()),
)

NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_TYPE = 'accepted_partnership'
NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_TYPE = 'declined_partnership'
NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_TYPE = 'requested_partnership'

NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_RECIPIENT_TYPE = 'accepted_partnership_recipient'
NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_RECIPIENT_TYPE = 'declined_partnership_recipient'
NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_RECIPIENT_TYPE = 'requested_partnership_recipient'
NOTIFICATION_TYPE_REQUEST_FOR_DELIVERY = 'request_for_delivery'

NOTIFICATION_TYPE_RECRUIT_JOB_TYPE = 'recruit'
NOTIFICATION_TYPE_GET_JOB_TYPE = 'get_job'
NOTIFICATION_TYPE_CHANGE_JOB_POSITION = 'changed_position'
NOTIFICATION_TYPE_CHANGE_JOB_POSITION_OWNER = 'changed_position_as_owner'
NOTIFICATION_TYPE_DISMISS_JOB = 'dismissed'
NOTIFICATION_TYPE_QUIT_JOB = 'quit'

NEW_DISCOUNT_TYPE = 'new_discount'
NEW_ORGANIZATION = 'new_organization'
NEW_DEVICE = 'new_device'
FOLLOWED_TO_ORGANIZATION_TYPE = 'followed_to_organization'
ORGANIZATION_FOLLOWED_TYPE = 'organization_followed'
SYSTEM_TYPE = 'system'
ORGANIZATION_MESSAGE_TYPE = 'organization_message'
ORGANIZATION_MESSAGE_SENDER_TYPE = 'sent_message'

ORGANIZATION_WITHDRAWAL_UNDER_REVIEW_TYPE = 'organization_withdrawal_under_review'
WITHDRAWAL_UNDER_REVIEW_TYPE = 'withdrawal_under_review'

ORGANIZATION_WITHDRAWAL_ACCEPTED_TYPE = 'organization_withdrawal_accepted'
WITHDRAWAL_ACCEPTED_TYPE = 'withdrawal_accepted'

ORGANIZATION_WITHDRAWAL_DECLINED_TYPE = 'organization_withdrawal_declined'
WITHDRAWAL_DECLINED_TYPE = 'withdrawal_declined'

ORGANIZATION_GAVE_TYPE = 'gave_organization'
ORGANIZATION_OWN_TYPE = 'owned_organization'

ATTENDANCE_IN = 'attendance_in'
ATTENDANCE_OUT = 'attendance_out'
CHECK_ATTENDANCE_IN = 'check_attendance_in'
CHECK_ATTENDANCE_OUT = 'check_attendance_out'

# Following three are no longer used
ACCEPT_DISCOUNT_TYPE = 'accept_discount'
ACCEPT_SELLER_DISCOUNT_TYPE = 'accepted_seller_discount'
DECLINE_DISCOUNT_TYPE = 'decline_discount'

WITHDRAW_CASHBACK_CLIENT = 'withdraw_cashback_client'
CHARGE_CASHBACK_CLIENT = 'charge_cashback_client'

WITHDRAW_CASHBACK_SELLER = 'withdraw_cashback_seller'
CHARGE_CASHBACK_SELLER = 'charge_cashback_seller'

NEW_CASHBACK = 'new_cashback'

REQUEST_ONLINE_ORDER_TYPE = 'requested_online_order'

ACCEPT_ORDER_TYPE = 'accepted_order'
DECLINE_ORDER_TYPE = 'declined_order'
REQUEST_ORDER_TYPE = 'requested_order'

ACCEPT_RENTAL_TYPE = 'accepted_rental'
DECLINE_RENTAL_TYPE = 'declined_rental'
REQUEST_RENTAL_TYPE = 'requested_rental'

REQUEST_RESUME_TYPE = 'requested_resume'

ACCEPT_ORDER_PAYMENT_TYPE = 'accepted_order_payment'
DECLINE_ORDER_PAYMENT_TYPE = 'declined_order_payment'

ACCEPT_RENTAL_PAYMENT_TYPE = 'accepted_rental_payment'
DECLINE_RENTAL_PAYMENT_TYPE = 'declined_rental_payment'

DECLINE_ACCEPTED_RENTAL_TYPE = 'declined_accepted_rental'
DECLINE_ACCEPTED_RENTAL_CLIENT_TYPE = 'declined_accepted_rental_client'

ACCEPT_ORDER_PAYMENT_CLIENT_TYPE = 'accepted_order_payment_client'
DECLINE_ORDER_PAYMENT_CLIENT_TYPE = 'declined_order_payment_client'

ACCEPT_RENTAL_PAYMENT_CLIENT_TYPE = 'accepted_rental_payment_client'
DECLINE_RENTAL_PAYMENT_CLIENT_TYPE = 'declined_rental_payment_client'

ACCEPT_ORDER_CLIENT_TYPE = 'accepted_order_client'
DECLINE_ORDER_CLIENT_TYPE = 'declined_order_client'
REQUEST_ORDER_CLIENT_TYPE = 'requested_order_client'

ACCEPTED_ONLINE_ORDER_CLIENT_TYPE = 'accepted_online_order_client'

ACCEPT_RENTAL_CLIENT_TYPE = 'accepted_rental_client'
DECLINE_RENTAL_CLIENT_TYPE = 'declined_rental_client'
REQUEST_RENTAL_CLIENT_TYPE = 'requested_rental_client'

ACTIVATE_RENTAL_TYPE = 'activated_rental'
ACTIVATE_RENTAL_CLIENT_TYPE = 'activated_rental_client'

ACTIVATE_TICKET_TYPE = 'activated_ticket'
ACTIVATE_TICKET_CLIENT_TYPE = 'activated_ticket_client'


REQUEST_RESUME_CLIENT_TYPE = 'requested_resume_client'

NEW_COMMENT_TYPE = 'new_comment'

NOTIFICATION_TYPE_AVAILABLE_DELIVERY = 'for_delivery'
NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION = 'for_delivery_for_organization'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE = 'accepted_by_delivery'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION = 'accepted_by_delivery_for_organization'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT = 'accepted_by_delivery_for_client'
NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT = 'sent_to_delivery_by_organization_for_client'
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE = 'rejected_by_delivery'
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT = 'rejected_by_delivery_for_client'
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION = 'rejected_by_delivery_for_organization'
NOTIFICATION_TYPE_DELIVERED = 'delivery_delivered'
NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT = 'delivery_delivered_for_client'
NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION = 'delivery_delivered_for_organization'

NOTIFICATION_TYPES = (
    (ACCEPT_ORDER_CLIENT_TYPE, ACCEPT_ORDER_CLIENT_TYPE),
    (ACCEPTED_ONLINE_ORDER_CLIENT_TYPE, ACCEPTED_ONLINE_ORDER_CLIENT_TYPE),
    (ACCEPT_RENTAL_CLIENT_TYPE, ACCEPT_RENTAL_CLIENT_TYPE),
    (DECLINE_ORDER_CLIENT_TYPE, DECLINE_ORDER_CLIENT_TYPE),
    (DECLINE_RENTAL_CLIENT_TYPE, DECLINE_RENTAL_CLIENT_TYPE),
    (REQUEST_ORDER_CLIENT_TYPE, REQUEST_ORDER_CLIENT_TYPE),
    (REQUEST_RENTAL_CLIENT_TYPE, REQUEST_RENTAL_CLIENT_TYPE),
    (ACTIVATE_RENTAL_TYPE, ACTIVATE_RENTAL_TYPE),
    (ACTIVATE_RENTAL_CLIENT_TYPE, ACTIVATE_RENTAL_CLIENT_TYPE),
    (ACTIVATE_TICKET_TYPE, ACTIVATE_TICKET_TYPE),
    (ACTIVATE_TICKET_CLIENT_TYPE, ACTIVATE_TICKET_CLIENT_TYPE),
    (REQUEST_RESUME_CLIENT_TYPE, REQUEST_RESUME_CLIENT_TYPE),
    (ACCEPT_ORDER_TYPE, ACCEPT_ORDER_TYPE),
    (ACCEPT_RENTAL_TYPE, ACCEPT_RENTAL_TYPE),
    (ACCEPT_ORDER_PAYMENT_TYPE, ACCEPT_ORDER_PAYMENT_TYPE),
    (ACCEPT_RENTAL_PAYMENT_TYPE, ACCEPT_RENTAL_PAYMENT_TYPE),
    (DECLINE_ORDER_PAYMENT_TYPE, DECLINE_ORDER_PAYMENT_TYPE),
    (DECLINE_RENTAL_PAYMENT_TYPE, DECLINE_RENTAL_PAYMENT_TYPE),
    (ACCEPT_ORDER_PAYMENT_CLIENT_TYPE, ACCEPT_ORDER_PAYMENT_CLIENT_TYPE),
    (DECLINE_ORDER_PAYMENT_CLIENT_TYPE, DECLINE_ORDER_PAYMENT_CLIENT_TYPE),
    (ACCEPT_RENTAL_PAYMENT_CLIENT_TYPE, ACCEPT_RENTAL_PAYMENT_CLIENT_TYPE),
    (DECLINE_RENTAL_PAYMENT_CLIENT_TYPE, DECLINE_RENTAL_PAYMENT_CLIENT_TYPE),
    (DECLINE_ACCEPTED_RENTAL_TYPE, DECLINE_ACCEPTED_RENTAL_TYPE),
    (DECLINE_ACCEPTED_RENTAL_CLIENT_TYPE, DECLINE_ACCEPTED_RENTAL_CLIENT_TYPE),
    (DECLINE_ORDER_TYPE, DECLINE_ORDER_TYPE),
    (DECLINE_RENTAL_TYPE, DECLINE_RENTAL_TYPE),
    (REQUEST_ONLINE_ORDER_TYPE, REQUEST_ONLINE_ORDER_TYPE),
    (REQUEST_ORDER_TYPE, REQUEST_ORDER_TYPE),
    (REQUEST_RENTAL_TYPE, REQUEST_RENTAL_TYPE),
    (REQUEST_RESUME_TYPE, REQUEST_RESUME_TYPE),
    (NEW_CASHBACK, NEW_CASHBACK),
    (WITHDRAW_CASHBACK_CLIENT, WITHDRAW_CASHBACK_CLIENT),
    (CHARGE_CASHBACK_CLIENT, CHARGE_CASHBACK_CLIENT),
    (WITHDRAW_CASHBACK_SELLER, WITHDRAW_CASHBACK_SELLER),
    (CHARGE_CASHBACK_SELLER, CHARGE_CASHBACK_SELLER),
    (CHECK_ATTENDANCE_IN, CHECK_ATTENDANCE_IN),
    (CHECK_ATTENDANCE_OUT, CHECK_ATTENDANCE_OUT),
    (ATTENDANCE_IN, ATTENDANCE_IN),
    (ATTENDANCE_OUT, ATTENDANCE_OUT),
    (ACCEPT_DISCOUNT_TYPE, ACCEPT_DISCOUNT_TYPE),
    (DECLINE_DISCOUNT_TYPE, DECLINE_DISCOUNT_TYPE),
    (NEW_DISCOUNT_TYPE, NEW_DISCOUNT_TYPE),
    (NEW_ORGANIZATION, NEW_ORGANIZATION),
    (NEW_DEVICE, NEW_DEVICE),
    (FOLLOWED_TO_ORGANIZATION_TYPE, FOLLOWED_TO_ORGANIZATION_TYPE),
    (ORGANIZATION_FOLLOWED_TYPE, ORGANIZATION_FOLLOWED_TYPE),
    (ORGANIZATION_WITHDRAWAL_UNDER_REVIEW_TYPE, ORGANIZATION_WITHDRAWAL_UNDER_REVIEW_TYPE),
    (WITHDRAWAL_UNDER_REVIEW_TYPE, WITHDRAWAL_UNDER_REVIEW_TYPE),
    (ORGANIZATION_WITHDRAWAL_ACCEPTED_TYPE, ORGANIZATION_WITHDRAWAL_ACCEPTED_TYPE),
    (WITHDRAWAL_ACCEPTED_TYPE, WITHDRAWAL_ACCEPTED_TYPE),
    (ORGANIZATION_WITHDRAWAL_DECLINED_TYPE, ORGANIZATION_WITHDRAWAL_DECLINED_TYPE),
    (WITHDRAWAL_DECLINED_TYPE, WITHDRAWAL_DECLINED_TYPE),
    (SYSTEM_TYPE, SYSTEM_TYPE),
    (NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_TYPE, NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_TYPE),
    (NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_TYPE, NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_TYPE),
    (NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_TYPE, NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_TYPE),
    (ACCEPT_SELLER_DISCOUNT_TYPE, ACCEPT_SELLER_DISCOUNT_TYPE),
    (NOTIFICATION_TYPE_GET_JOB_TYPE, NOTIFICATION_TYPE_GET_JOB_TYPE),
    (NOTIFICATION_TYPE_RECRUIT_JOB_TYPE, NOTIFICATION_TYPE_RECRUIT_JOB_TYPE),
    (NOTIFICATION_TYPE_CHANGE_JOB_POSITION, NOTIFICATION_TYPE_CHANGE_JOB_POSITION),
    (NOTIFICATION_TYPE_DISMISS_JOB, NOTIFICATION_TYPE_DISMISS_JOB),
    (NOTIFICATION_TYPE_QUIT_JOB, NOTIFICATION_TYPE_QUIT_JOB),
    (NOTIFICATION_TYPE_CHANGE_JOB_POSITION_OWNER, NOTIFICATION_TYPE_CHANGE_JOB_POSITION_OWNER),
    (ORGANIZATION_MESSAGE_TYPE, ORGANIZATION_MESSAGE_TYPE),
    (ORGANIZATION_GAVE_TYPE, ORGANIZATION_GAVE_TYPE),
    (ORGANIZATION_OWN_TYPE, ORGANIZATION_OWN_TYPE),
    (ORGANIZATION_MESSAGE_SENDER_TYPE, ORGANIZATION_MESSAGE_SENDER_TYPE),
    (NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_RECIPIENT_TYPE, NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_RECIPIENT_TYPE),
    (NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_RECIPIENT_TYPE, NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_RECIPIENT_TYPE),
    (NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_RECIPIENT_TYPE, NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_RECIPIENT_TYPE),
    (NOTIFICATION_TYPE_AVAILABLE_DELIVERY, NOTIFICATION_TYPE_AVAILABLE_DELIVERY),
    (NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE, NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE),
    (NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT,
     NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT),
    (NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT,
     NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT),
    (NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE, NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE),
    (NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT,
     NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT),
    (NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION,
     NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION),
    (NOTIFICATION_TYPE_DELIVERED, NOTIFICATION_TYPE_DELIVERED),
    (NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT, NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT),
    (NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION, NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION),
    (NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION, NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION),
    (NEW_COMMENT_TYPE, NEW_COMMENT_TYPE),
)

# ______________________RUSSIAN___________________________#
NEW_COMMENT_TITLE_RU = 'У вас новый комментарий'
NEW_COMMENT_DESCRIPTION = '{comment_text}'

ACCEPT_ORDER_TITLE_RU = 'Вы приняли заказ #{transaction_id}'
DECLINE_ORDER_TITLE_RU = 'Вы отменили заказ #{transaction_id}'
REQUEST_ORDER_TITLE_RU = 'У вас новый заказ #{transaction_id}'

ACCEPT_RENTAL_TITLE_RU = 'Вы приняли заказ аренды #{transaction_id}'
DECLINE_RENTAL_TITLE_RU = 'Вы отменили заказ аренды #{transaction_id}'
REQUEST_RENTAL_TITLE_RU = 'У вас новый заказ аренды #{transaction_id}'

REQUEST_RESUME_TITLE_RU = 'У вас новый запрос на Вакансию: {resume_name}'

DECLINE_ORDER_PAYMENT_TITLE_RU = 'Клиент отклонил оплату за заказ #{transaction_id}'

ACCEPT_RENTAL_PAYMENT_TITLE_RU = 'Клиент оплатил заказ, завершите сделку #{transaction_id}'
DECLINE_RENTAL_PAYMENT_TITLE_RU = 'Клиент отклонил оплату за заказ #{transaction_id}'

ACCEPT_RENTAL_SALE_TITLE_RU = 'У вас новая аренда #{transaction_id}'
ACCEPT_RENTAL_SALE_CLIENT_TITLE_RU = 'Спасибо Вам за аренду !!! Ждём вас по этому чеку.'

DECLINE_ACCEPTED_RENTAL_TITLE_RU = 'Вы отменили сделку аренды, возвращение оплаты #{transaction_id}'
DECLINE_ACCEPTED_RENTAL_CLIENT_TITLE_RU = 'Вам отменили сделку аренды, возвращение оплаты #{transaction_id}'

ACCEPT_ORDER_PAYMENT_CLIENT_TITLE_RU = 'Ваш заказ оплачен !!! Наши сотрудники свяжутся с Вами. #{transaction_id}'
DECLINE_ORDER_PAYMENT_CLIENT_TITLE_RU = 'Вы отклонили оплату за заказ #{transaction_id}'

ACCEPT_RENTAL_PAYMENT_CLIENT_TITLE_RU = 'Поздравляем, Ваш заказ оплачен! Воспользуйтесь арендой, показав данный чек. #{transaction_id}'
DECLINE_RENTAL_PAYMENT_CLIENT_TITLE_RU = 'Вы отклонили оплату за аренду #{transaction_id}'

ACCEPT_ORDER_CLIENT_TITLE_RU = 'Ваш заказ приняли #{transaction_id}'
DECLINE_ORDER_CLIENT_TITLE_RU = 'Вам отменили заказ #{transaction_id}'
REQUEST_ORDER_CLIENT_TITLE_RU = 'Спасибо Вам за заказ !!! Наши сотрудники свяжутся с Вами.'

ACCEPT_ONLINE_ORDER_CLIENT_TITLE_RU = 'Ваш заказ готов к оплате #{transaction_id}'

ACCEPT_RENTAL_CLIENT_TITLE_RU = 'Ваш заказ аренды готов к оплате #{transaction_id}'
DECLINE_RENTAL_CLIENT_TITLE_RU = 'Вам отменили заказ аренды #{transaction_id}'
REQUEST_RENTAL_CLIENT_TITLE_RU = 'Спасибо Вам за заказ #{transaction_id} !!! Ждём подтверждения к оплате аренды.'

REQUEST_RESUME_CLIENT_TITLE_RU = 'Спасибо Вам за запрос ! Кандидат  свяжется с Вами по вакансии:: {resume_name}'
RESUME_DESCRIPTION_RU = 'Оплата от: {salary_from} {currency}'

ACTIVATE_RENTAL_CLIENT_TITLE_RU = 'Ваш заказ аренды активирован #{transaction_id}'
ACTIVATE_RENTAL_TITLE_RU = 'Вы активировали заказ аренды #{transaction_id}'

ACTIVATE_TICKET_CLIENT_TITLE_RU = 'Ваш билет активирован #{transaction_id}'
ACTIVATE_TICKET_TITLE_RU = 'Вы активировали билет #{transaction_id}'

ORDER_DESCRIPTION_RU = 'Сумма заказа: {total_price} {currency}'
RENTAL_DESCRIPTION_RU = 'Сумма заказа: {total_price} {currency}'

ATTENDANCE_IN_TITLE_RU = 'Вход {organization}'
ATTENDANCE_OUT_TITLE_RU = 'Выход {organization}'
CHECK_ATTENDANCE_IN_TITLE_RU = 'Пропуск на вход {organization}'
CHECK_ATTENDANCE_OUT_TITLE_RU = 'Пропуск на выход {organization}'

ATTENDANCE_DESCRIPTION_RU = ' '

FOLLOWED_TO_ORGANIZATION_TITLE_RU = 'На вашу организацию подписались'
BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION_RU = 'На вашу организацию подписались'
ORGANIZATION_FOLLOWED_TITLE_RU = 'Вы подписались на организацию'
BG_ORGANIZATION_FOLLOWED_DESCRIPTION_RU = 'Вы подписались'
DISCOUNT_COMPLETE_USER_TITLE_RU = 'Вам провели скидку {discount_percent} %'
DISCOUNT_COMPLETE_DESCRIPTION_RU = 'Итого со скидкой: {final_amount} {currency}'
DISCOUNT_COMPLETE_TITLE_RU = 'Вы провели скидку {discount_percent} %'

NEW_DISCOUNT_TITLE_RU = 'Доступна новая скидка {percent} %'
NEW_CASHBACK_TITLE_RU = 'Доступен новый кэшбэк {percent} %'

NEW_DISCOUNT_DESCRIPTION_RU = '{address} '
PARTNERSHIP_REQUEST_TITLE_RU = '{sender_organization} запрашивает стать партнером {recipient_organization}'
PARTNERSHIP_REQUEST_DESCRIPTION_RU = '{address} '
SUBSCRIPTION_NOTIFICATION_DESCRIPTION_RU = '{address} '
TRANSACTION_DECLINED_NOTIFICATION_TITLE_RU = 'Вам отменили сделку'
YOU_DECLINED_NOTIFICATION_TITLE_RU = 'Вы отменили сделку'
TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION_RU = 'Скидка {savings} {currency}'

NEW_ORGANIZATION_TITLE_RU = 'Новая организация доступна для вас'
NEW_ORGANIZATION_DESCRIPTION_RU = '{organization_title} '

NEW_DEVICE_TITLE_RU = 'Новая активация пользователя'
NEW_DEVICE_DESCRIPTION_RU = '{device_title}'

RECRUIT_JOB_TITLE_RU = 'Вы приняли на работу'
RECRUIT_JOB_DESCRIPTION_RU = '{position} '

GET_JOB_TITLE_RU = 'Вас приняли на работу'
GET_JOB_DESCRIPTION_RU = '{position} '

CHANGE_JOB_POSITION_TITLE_RU = 'Вас назначили на новую должность'
CHANGE_JOB_POSITION_DESCRIPTION_RU = '{old_position} на {new_position}'

CHANGE_JOB_POSITION_OWNER_TITLE_RU = 'Вы назначили другую должность'
CHANGE_JOB_POSITION_OWNER_DESCRIPTION_RU = '{old_position} на {new_position}'

QUIT_JOB_TITLE_RU = 'Вас уволили с работы'
QUIT_JOB_DESCRIPTION_RU = '{position} '

DISMISS_JOB_TITLE_RU = 'Вы уволили с работы'
DISMISS_JOB_DESCRIPTION_RU = '{position} '

ORGANIZATION_MESSAGE_TITLE_RU = 'Сообщение от '
ORGANIZATION_MESSAGE_PARTNERS_TITLE_RU = 'Сообщение для партнеров '
ORGANIZATION_MESSAGE_PARTNERS_FOLLOWERS_TITLE_RU = 'Сообщение подписчикам партнеров '
ORGANIZATION_MESSAGE_DESCRIPTION_RU = '{content} '
ORGANIZATION_OWNER_MESSAGE_TITLE_RU = 'Вы отправили сообщение'
ORGANIZATION_OWNER_MESSAGE_PARTNERS_TITLE_RU = 'Вы отправили сообщение партнерам'
ORGANIZATION_OWNER_MESSAGE_PARTNERS_FOLLOWERS_TITLE_RU = 'Вы отправили сообщение подписчикам партнеров'

ORGANIZATION_UNDER_REVIEW_WITHDRAWAL_TITLE_RU = 'Ваш вывод на рассмотрении #{transaction_id}'
UNDER_REVIEW_WITHDRAWAL_TITLE_RU = 'Вы передали вывод на рассмотрение #{transaction_id}'
ORGANIZATION_ACCEPTED_WITHDRAWAL_TITLE_RU = 'Поздравляем Ваш вывод завершен #{transaction_id}'
ACCEPTED_WITHDRAWAL_TITLE_RU = 'Поздравляем вы завершили вывод #{transaction_id}'
ORGANIZATION_DECLINED_WITHDRAWAL_TITLE_RU = 'Ваш вывод отменен #{transaction_id}'
DECLINED_WITHDRAWAL_TITLE_RU = 'Вы отменили рассмотрения вывода #{transaction_id}'
WITHDRAWAL_DESCRIPTION_RU = 'Сумма вывода: {total_withdrawal} {currency}'

ORGANIZATION_GAVE_TITLE_RU = 'Вы передали права собственника'
ORGANIZATION_GAVE_DESCRIPTION_RU = ' '

ORGANIZATION_OWN_TITLE_RU = 'Поздравляем Вы стали собственником'
ORGANIZATION_OWN_DESCRIPTION_RU = ' '

WITHDRAW_CASHBACK_CLIENT_TITLE_RU = 'Поздравляем Вам сняли {amount} {currency} с кешбэка'
CHARGE_CASHBACK_CLIENT_TITLE_RU = 'Поздравляем вам начислили кешбэк {amount} {currency}'

WITHDRAW_CASHBACK_SELLER_TITLE_RU = 'Вы сняли {amount} {currency} с кэшбэка'
CHARGE_CASHBACK_SELLER_TITLE_RU = 'Вы начислили кэшбэк {amount} {currency}'

NOTIFICATION_DELIVERY_AVAILABLE_TITLE_RU = 'Доступен новый заказ!!!'
NOTIFICATION_DELIVERY_AVAILABLE_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION_TITLE_RU = 'Курьерская служба может доставить ваш заказ'
NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_TITLE_RU = 'Вы взяли заказ к доставке'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT_TITLE_RU = 'Ваш заказ отправлен в курьерскую службу. С вами свяжутся '
NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT_TITLE_RU = 'Ваш заказ в пути'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_TITLE_RU = 'Ваш заказ взяли к доставке'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_DESCRIPTION_RU = ''

NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_TITLE_RU = 'Вы отменили заказ'
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT_TITLE_RU = 'Доставка Вашего заказа отменена'
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_TITLE_RU = 'Доставка Вашего заказа отменена'
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_DELIVERED_TITLE_RU = ''
NOTIFICATION_TYPE_DELIVERED_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT_TITLE_RU = 'Ваш заказ доставлен'
NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT_DESCRIPTION_RU = ''
NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION_TITLE_RU = 'Ваш заказ доставлен'
NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION_DESCRIPTION_RU = ''
# _______________________ ENGLISH _______________________#
NEW_COMMENT_TITLE_EN = 'You have a new comment'

ACCEPT_ORDER_TITLE_EN = 'You accepted order #{transaction_id}'
DECLINE_ORDER_TITLE_EN = 'You canceled order #{transaction_id}'
REQUEST_ORDER_TITLE_EN = 'You got new order #{transaction_id}'

ACCEPT_RENTAL_TITLE_EN = 'You accepted rental order #{transaction_id}'
DECLINE_RENTAL_TITLE_EN = 'You canceled rental order #{transaction_id}'
REQUEST_RENTAL_TITLE_EN = 'You got new rent order #{transaction_id}'

REQUEST_RESUME_TITLE_EN = 'You have vacancy request for the position: {resume_name}'

DECLINE_ORDER_PAYMENT_TITLE_EN = 'Customer canceled payment #{transaction_id}'

ACCEPT_RENTAL_PAYMENT_TITLE_EN = 'Customer has paid for the order, complete deal #{transaction_id}'
DECLINE_RENTAL_PAYMENT_TITLE_EN = 'Customer canceled rent payment #{transaction_id}'

ACCEPT_RENTAL_SALE_TITLE_EN = 'You have a new rent #{transaction_id}'
ACCEPT_RENTAL_SALE_CLIENT_TITLE_EN = 'Thank you for the rental !!! Looking forward to seeing you on this check.'

DECLINE_ACCEPTED_RENTAL_TITLE_EN = 'You canceled rent order, payment refunding #{transaction_id}'
DECLINE_ACCEPTED_RENTAL_CLIENT_TITLE_EN = 'Your rent order canceled, payment refunding #{transaction_id}'

ACCEPT_ORDER_PAYMENT_CLIENT_TITLE_EN = 'Your order paid !!! We will contact you. #{transaction_id}'
DECLINE_ORDER_PAYMENT_CLIENT_TITLE_EN = 'You canceled payment #{transaction_id}'

ACCEPT_RENTAL_PAYMENT_CLIENT_TITLE_EN = 'Congratulations, your order paid! Use this receipt to get rental. #{transaction_id}'
DECLINE_RENTAL_PAYMENT_CLIENT_TITLE_EN = 'You canceled rent payment #{transaction_id}'

ACCEPT_ORDER_CLIENT_TITLE_EN = 'Your order accepted #{transaction_id}'
DECLINE_ORDER_CLIENT_TITLE_EN = 'Your order has been canceled #{transaction_id}'
REQUEST_ORDER_CLIENT_TITLE_EN = 'Thank you for your order !!! We will contact you.'
ORDER_DESCRIPTION_EN = 'Order price: {total_price} {currency}'

ACCEPT_ONLINE_ORDER_CLIENT_TITLE_EN = 'Your order is ready for payment #{transaction_id}'

ACCEPT_RENTAL_CLIENT_TITLE_EN = 'Your rent order is ready for payment #{transaction_id}'
DECLINE_RENTAL_CLIENT_TITLE_EN = 'Your rental order canceled #{transaction_id}'
REQUEST_RENTAL_CLIENT_TITLE_EN = 'Thank you for your order #{transaction_id} !!! Waiting for confirmation to pay the rent.'
RENTAL_DESCRIPTION_EN = 'Order price: {total_price} {currency}'

REQUEST_RESUME_CLIENT_TITLE_EN = 'Thank you for your request ! The candidate will contact you for position: {resume_name}'
RESUME_DESCRIPTION_EN = 'Salary from: {salary_from} {currency}'

ACTIVATE_RENTAL_TITLE_EN = 'You activated rent order #{transaction_id}'
ACTIVATE_RENTAL_CLIENT_TITLE_EN = 'Your rent order is activated #{transaction_id}'

ACTIVATE_TICKET_TITLE_EN = 'You activated ticket #{transaction_id}'
ACTIVATE_TICKET_CLIENT_TITLE_EN = 'Your ticket is activated #{transaction_id}'

ATTENDANCE_IN_TITLE = 'Input {organization}'
ATTENDANCE_OUT_TITLE = 'Exit {organization}'
CHECK_ATTENDANCE_IN_TITLE = 'Entry pass {organization}'
CHECK_ATTENDANCE_OUT_TITLE = 'Exit pass {organization}'

ATTENDANCE_DESCRIPTION = ' '

FOLLOWED_TO_ORGANIZATION_TITLE = 'Subscribed to your organization'
BG_FOLLOWED_TO_ORGANIZATION_DESCRIPTION = 'Subscribed to your organization'
ORGANIZATION_FOLLOWED_TITLE = 'You subscribed to'
BG_ORGANIZATION_FOLLOWED_DESCRIPTION = 'You are subscribed'
DISCOUNT_COMPLETE_USER_TITLE = 'You got a discount {discount_percent} %'
DISCOUNT_COMPLETE_DESCRIPTION = 'Total with discount: {final_amount} {currency}'
DISCOUNT_COMPLETE_TITLE = 'You made a discount {discount_percent} %'

ORGANIZATION_UNDER_REVIEW_WITHDRAWAL_TITLE_EN = 'Your withdrawal is under review #{transaction_id}'
UNDER_REVIEW_WITHDRAWAL_TITLE_EN = 'You submitted a withdrawal for review #{transaction_id}'
ORGANIZATION_ACCEPTED_WITHDRAWAL_TITLE_EN = 'Congratulations, your withdrawal is complete #{transaction_id}'
ACCEPTED_WITHDRAWAL_TITLE_EN = 'Congratulations, you have completed the withdrawal #{transaction_id}'
ORGANIZATION_DECLINED_WITHDRAWAL_TITLE_EN = 'Your withdrawal has been canceled #{transaction_id}'
DECLINED_WITHDRAWAL_TITLE_EN = 'You have canceled the review of withdrawal #{transaction_id}'
WITHDRAWAL_DESCRIPTION_EN = 'Withdrawal amount: {total_withdrawal} {currency}'

NEW_DISCOUNT_TITLE = 'New discount available {percent} %'
NEW_CASHBACK_TITLE = 'New cashback available {percent} %'

NEW_DISCOUNT_DESCRIPTION = '{address} '
PARTNERSHIP_REQUEST_TITLE = '{sender_organization} wants to become a partner {recipient_organization}'
PARTNERSHIP_REQUEST_DESCRIPTION = '{address} '
SUBSCRIPTION_NOTIFICATION_DESCRIPTION = '{address} '
TRANSACTION_DECLINED_NOTIFICATION_TITLE = 'Your deal was canceled'
YOU_DECLINED_NOTIFICATION_TITLE = 'You canceled the deal'
TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION = 'Discount {savings} {currency}'

NEW_ORGANIZATION_TITLE = 'New organization is available for you '
NEW_ORGANIZATION_DESCRIPTION = '{organization_title} '

NEW_DEVICE_TITLE = 'New user activated'
NEW_DEVICE_DESCRIPTION = '{device_title}'

RECRUIT_JOB_TITLE = 'You hired an employee'
RECRUIT_JOB_DESCRIPTION = '{position} '

GET_JOB_TITLE = 'You were hired as an employee'
GET_JOB_DESCRIPTION = '{position} '

CHANGE_JOB_POSITION_TITLE = 'You have been appointed to new position'
CHANGE_JOB_POSITION_DESCRIPTION = '{old_position} на {new_position}'

CHANGE_JOB_POSITION_OWNER_TITLE = 'You have appointed different position'
CHANGE_JOB_POSITION_OWNER_DESCRIPTION = '{old_position} to {new_position}'

QUIT_JOB_TITLE = 'You got fired from'
QUIT_JOB_DESCRIPTION = '{position} '

DISMISS_JOB_TITLE = 'You fired from'
DISMISS_JOB_DESCRIPTION = '{position} '

ORGANIZATION_MESSAGE_TITLE = 'Message from '
ORGANIZATION_MESSAGE_PARTNERS_TITLE = 'Message for partners'
ORGANIZATION_MESSAGE_PARTNERS_FOLLOWERS_TITLE = 'Message to subscribers of partners'
ORGANIZATION_MESSAGE_DESCRIPTION = '{content} '
ORGANIZATION_OWNER_MESSAGE_TITLE = 'You have sent a message'
ORGANIZATION_OWNER_MESSAGE_PARTNERS_TITLE = 'You have sent a message to partners'
ORGANIZATION_OWNER_MESSAGE_PARTNERS_FOLLOWERS_TITLE = 'You have sent message to your partners subscribers'

ORGANIZATION_GAVE_TITLE = 'You have transferred ownership rights'
ORGANIZATION_GAVE_DESCRIPTION = ' '

ORGANIZATION_OWN_TITLE = 'Congratulations, you became an owner of'
ORGANIZATION_OWN_DESCRIPTION = ' '

WITHDRAW_CASHBACK_CLIENT_TITLE = 'Congratulations you have paid,{amount} {currency} from cashback'
CHARGE_CASHBACK_CLIENT_TITLE = ' Congratulations you received cashback {amount} {currency}'

WITHDRAW_CASHBACK_SELLER_TITLE = 'You took transfer {amount} {currency} from cashback'
CHARGE_CASHBACK_SELLER_TITLE = 'You have credited cashback {amount} {currency}'
NOTIFICATION_DELIVERY_AVAILABLE_TITLE_EN = 'New delivery order available!!!'
NOTIFICATION_DELIVERY_AVAILABLE_DESCRIPTION_EN = ' '

NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_TITLE_EN = 'You took an order for delivery'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION_TITLE_EN = 'Courier service can deliver your order'
NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT_TITLE_EN = 'Your order already sent to delivery service and will contact with you.'
NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT_TITLE_EN = 'Your order on the way'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_TITLE_EN = 'Your order was accepted by delivery organization'
NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_DESCRIPTION_EN = ''

NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_TITLE_EN = 'You canceled order '
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT_TITLE_EN = 'Delivery of your order canceled'
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_TITLE_EN = 'Delivery of your order canceled'
NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_DELIVERED_TITLE_EN = ''
NOTIFICATION_TYPE_DELIVERED_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT_TITLE_EN = 'Your order delivered'
NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT_DESCRIPTION_EN = ''
NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION_TITLE_EN = 'Your order delivered'
NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION_DESCRIPTION_EN = ''


def get_titles_descriptions_from_type(notification_type: str, extra_data=None) -> dict:
    if not extra_data:
        extra_data = dict(empty=True)

    notification_str = dict()

    if notification_type == NEW_ORGANIZATION:
        notification_str = dict(title=NEW_ORGANIZATION_TITLE,
                                description=NEW_ORGANIZATION_DESCRIPTION.format(
                                    organization_title=extra_data.get('organization_title')),
                                title_ru=NEW_ORGANIZATION_TITLE_RU,
                                description_ru=NEW_ORGANIZATION_DESCRIPTION_RU.format(
                                    organization_title=extra_data.get('organization_title')))

    elif notification_type == NEW_DEVICE:
        notification_str = dict(title=NEW_DEVICE_TITLE,
                                description=NEW_DEVICE_DESCRIPTION.format(
                                    device_title=extra_data.get('device_title')),
                                title_ru=NEW_DEVICE_TITLE_RU,
                                description_ru=NEW_DEVICE_DESCRIPTION_RU.format(
                                    device_title=extra_data.get('device_title'),
                                    location=extra_data.get('location')),
                                    created_at=extra_data.get('created_at'))

    elif notification_type == ORGANIZATION_OWN_TYPE:
        notification_str = dict(title=ORGANIZATION_OWN_TITLE,
                                description=ORGANIZATION_OWN_DESCRIPTION,
                                title_ru=ORGANIZATION_OWN_TITLE_RU,
                                description_ru=ORGANIZATION_OWN_DESCRIPTION)

    elif notification_type == ORGANIZATION_GAVE_TYPE:
        notification_str = dict(title=ORGANIZATION_GAVE_TITLE,
                                description=ORGANIZATION_GAVE_DESCRIPTION,
                                title_ru=ORGANIZATION_GAVE_TITLE_RU,
                                description_ru=ORGANIZATION_GAVE_DESCRIPTION)

    elif notification_type == ORGANIZATION_MESSAGE_TYPE:
        title_ru = ''
        title = ''
        if extra_data.get('message_to') == 'organization_followers':
            title = ORGANIZATION_MESSAGE_TITLE
            title_ru = ORGANIZATION_MESSAGE_TITLE_RU
        elif extra_data.get('message_to') == 'partners_followers':
            title = ORGANIZATION_MESSAGE_PARTNERS_FOLLOWERS_TITLE
            title_ru = ORGANIZATION_MESSAGE_PARTNERS_FOLLOWERS_TITLE_RU
        elif extra_data.get('message_to') == 'partners_members':
            title = ORGANIZATION_MESSAGE_PARTNERS_TITLE
            title_ru = ORGANIZATION_MESSAGE_PARTNERS_TITLE_RU
        notification_str = dict(title=title,
                                description=ORGANIZATION_MESSAGE_DESCRIPTION.format(content=extra_data.get('content')),
                                title_ru=title_ru,
                                description_ru=ORGANIZATION_MESSAGE_DESCRIPTION_RU.format(
                                    content=extra_data.get('content')))
    elif notification_type == ORGANIZATION_MESSAGE_SENDER_TYPE:
        title_ru = ''
        title = ''
        if extra_data.get('message_to') == 'organization_followers':
            title = ORGANIZATION_OWNER_MESSAGE_TITLE
            title_ru = ORGANIZATION_OWNER_MESSAGE_TITLE_RU
        elif extra_data.get('message_to') == 'partners_followers':
            title = ORGANIZATION_OWNER_MESSAGE_PARTNERS_FOLLOWERS_TITLE
            title_ru = ORGANIZATION_OWNER_MESSAGE_PARTNERS_FOLLOWERS_TITLE_RU
        elif extra_data.get('message_to') == 'partners_members':
            title = ORGANIZATION_OWNER_MESSAGE_PARTNERS_TITLE
            title_ru = ORGANIZATION_OWNER_MESSAGE_PARTNERS_TITLE_RU
        notification_str = dict(title=title,
                                description=ORGANIZATION_MESSAGE_DESCRIPTION.format(content=extra_data.get('content')),
                                title_ru=title_ru,
                                description_ru=ORGANIZATION_MESSAGE_DESCRIPTION_RU.format(
                                    content=extra_data.get('content')))

    elif notification_type == NEW_CASHBACK:
        notification_str = dict(title=NEW_CASHBACK_TITLE.format(percent=extra_data.get('cashback')),
                                description=NEW_DISCOUNT_DESCRIPTION.format(address=extra_data.get('address')),
                                title_ru=NEW_CASHBACK_TITLE_RU.format(percent=extra_data.get('cashback')),
                                description_ru=NEW_DISCOUNT_DESCRIPTION_RU.format(address=extra_data.get('address')))

    elif notification_type == NEW_DISCOUNT_TYPE:
        notification_str = dict(
            title=NEW_DISCOUNT_TITLE.format(percent=extra_data.get('percent')),
            title_ru=NEW_DISCOUNT_TITLE_RU.format(percent=extra_data.get('percent')),
            description=NEW_DISCOUNT_DESCRIPTION.format(address=extra_data.get('address')),
            description_ru=NEW_DISCOUNT_DESCRIPTION_RU.format(address=extra_data.get('address')))

    elif notification_type == WITHDRAW_CASHBACK_CLIENT:
        notification_str = dict(
            title=WITHDRAW_CASHBACK_CLIENT_TITLE.format(amount=extra_data.get('amount'),
                                                        currency=extra_data.get('currency')),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data.get('final_amount'),
                                                             currency=extra_data.get('currency')),
            title_ru=WITHDRAW_CASHBACK_CLIENT_TITLE_RU.format(amount=extra_data.get('amount'),
                                                              currency=extra_data.get('currency')),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data.get('final_amount'),
                                                                   currency=extra_data.get('currency')))
    elif notification_type == CHARGE_CASHBACK_CLIENT:
        notification_str = dict(
            title=CHARGE_CASHBACK_CLIENT_TITLE.format(amount=extra_data.get('amount'),
                                                      currency=extra_data.get('currency')),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data.get('final_amount'),
                                                             currency=extra_data.get('currency')),
            title_ru=CHARGE_CASHBACK_CLIENT_TITLE_RU.format(amount=extra_data.get('amount'),
                                                            currency=extra_data.get('currency')),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data.get('final_amount'),
                                                                   currency=extra_data.get('currency')))
    elif notification_type == WITHDRAW_CASHBACK_SELLER:
        notification_str = dict(
            title=WITHDRAW_CASHBACK_SELLER_TITLE.format(amount=extra_data.get('amount'),
                                                        currency=extra_data.get('currency')),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data.get('final_amount'),
                                                             currency=extra_data.get('currency')),
            title_ru=WITHDRAW_CASHBACK_SELLER_TITLE_RU.format(amount=extra_data.get('amount'),
                                                              currency=extra_data.get('currency')),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data.get('final_amount'),
                                                                   currency=extra_data.get('currency')))
    elif notification_type == CHARGE_CASHBACK_SELLER:
        notification_str = dict(
            title=CHARGE_CASHBACK_SELLER_TITLE.format(amount=extra_data.get('amount'),
                                                      currency=extra_data.get('currency')),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data.get('final_amount'),
                                                             currency=extra_data.get('currency')),
            title_ru=CHARGE_CASHBACK_SELLER_TITLE_RU.format(amount=extra_data.get('amount'),
                                                            currency=extra_data.get('currency')),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data.get('final_amount'),
                                                                   currency=extra_data.get('currency')))
    elif notification_type == CHECK_ATTENDANCE_IN:
        notification_str = dict(title=CHECK_ATTENDANCE_IN_TITLE.format(organization=extra_data.get('organization')),
                                description=ATTENDANCE_DESCRIPTION,
                                title_ru=CHECK_ATTENDANCE_IN_TITLE_RU.format(
                                    organization=extra_data.get('organization')),
                                description_ru=ATTENDANCE_DESCRIPTION_RU)

    elif notification_type == CHECK_ATTENDANCE_OUT:
        notification_str = dict(title=CHECK_ATTENDANCE_OUT_TITLE.format(organization=extra_data.get('organization')),
                                description=ATTENDANCE_DESCRIPTION,
                                title_ru=CHECK_ATTENDANCE_OUT_TITLE_RU.format(
                                    organization=extra_data.get('organization')),
                                description_ru=ATTENDANCE_DESCRIPTION_RU)

    elif notification_type == ATTENDANCE_IN:
        notification_str = dict(title=ATTENDANCE_IN_TITLE.format(organization=extra_data.get('organization')),
                                description=ATTENDANCE_DESCRIPTION,
                                title_ru=ATTENDANCE_IN_TITLE_RU.format(organization=extra_data.get('organization')),
                                description_ru=ATTENDANCE_DESCRIPTION_RU)

    elif notification_type == ATTENDANCE_OUT:
        notification_str = dict(title=ATTENDANCE_OUT_TITLE.format(organization=extra_data.get('organization')),
                                description=ATTENDANCE_DESCRIPTION,
                                title_ru=ATTENDANCE_OUT_TITLE_RU.format(organization=extra_data.get('organization')),
                                description_ru=ATTENDANCE_DESCRIPTION_RU)

    elif notification_type == ACCEPT_DISCOUNT_TYPE:
        notification_str = dict(
            title=DISCOUNT_COMPLETE_USER_TITLE.format(discount_percent=extra_data.get('discount_percent')),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data.get('final_amount'),
                                                             currency=extra_data.get('currency')),
            title_ru=DISCOUNT_COMPLETE_USER_TITLE_RU.format(discount_percent=extra_data.get('discount_percent')),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data.get('final_amount'),
                                                                   currency=extra_data.get('currency')))


    elif notification_type == ACCEPT_SELLER_DISCOUNT_TYPE:
        notification_str = dict(
            title=DISCOUNT_COMPLETE_TITLE.format(discount_percent=extra_data.get('discount_percent')),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data.get('final_amount'),
                                                             currency=extra_data.get('currency')),
            title_ru=DISCOUNT_COMPLETE_TITLE_RU.format(discount_percent=extra_data.get('discount_percent')),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data.get('final_amount'),
                                                                   currency=extra_data.get('currency')))

    elif notification_type == DECLINE_DISCOUNT_TYPE:
        if extra_data.get('recipient') == 'client':
            notification_str = dict(
                title=TRANSACTION_DECLINED_NOTIFICATION_TITLE,
                description=TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION.format(savings=extra_data.get('savings'),
                                                                                 currency=extra_data.get('currency')),
                title_ru=TRANSACTION_DECLINED_NOTIFICATION_TITLE_RU,
                description_ru=TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION.format(savings=extra_data.get('savings'),
                                                                                    currency=extra_data.get(
                                                                                        'currency')))
        else:
            notification_str = dict(
                title=YOU_DECLINED_NOTIFICATION_TITLE,
                description=TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION.format(savings=extra_data.get('savings'),
                                                                                 currency=extra_data.get('currency')),
                title_ru=YOU_DECLINED_NOTIFICATION_TITLE_RU,
                description_ru=TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION.format(savings=extra_data.get('savings'),
                                                                                    currency=extra_data.get(
                                                                                        'currency')))

    elif notification_type == FOLLOWED_TO_ORGANIZATION_TYPE:
        notification_str = dict(title=FOLLOWED_TO_ORGANIZATION_TITLE,
                                description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(
                                    address=extra_data.get('address')),
                                title_ru=FOLLOWED_TO_ORGANIZATION_TITLE_RU,
                                description_ru=SUBSCRIPTION_NOTIFICATION_DESCRIPTION_RU.format(
                                    address=extra_data.get('address')))

    elif notification_type == ORGANIZATION_FOLLOWED_TYPE:
        notification_str = dict(title=ORGANIZATION_FOLLOWED_TITLE,
                                description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(
                                    address=extra_data.get('address')),
                                title_ru=ORGANIZATION_FOLLOWED_TITLE_RU,
                                description_ru=SUBSCRIPTION_NOTIFICATION_DESCRIPTION_RU.format(
                                    address=extra_data.get('address')))

    elif notification_type == NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_TYPE:
        notification_str = dict(
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data.get('sender_organization'),
                                                   recipient_organization=extra_data.get('recipient_organization')),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data.get('address')),
            title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data.get('sender_organization'),
                                                         recipient_organization=extra_data.get(
                                                             'recipient_organization')),
            description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data.get('address')))

    elif notification_type == NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_TYPE:
        notification_str = dict(
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data.get('sender_organization'),
                                                   recipient_organization=extra_data.get('recipient_organization')),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data.get('address')),
            title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data.get('sender_organization'),
                                                         recipient_organization=extra_data.get(
                                                             'recipient_organization')),
            description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data.get('address')))

    elif notification_type == NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_TYPE:
        notification_str = dict(
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data.get('sender_organization'),
                                                   recipient_organization=extra_data.get('recipient_organization')),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data.get('address')),
            title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data.get('sender_organization'),
                                                         recipient_organization=extra_data.get(
                                                             'recipient_organization')),
            description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data.get('address')))

    elif notification_type == NOTIFICATION_TYPE_RECRUIT_JOB_TYPE:
        notification_str = dict(title=RECRUIT_JOB_TITLE,
                                description=RECRUIT_JOB_DESCRIPTION.format(position=extra_data.get('position')),
                                title_ru=RECRUIT_JOB_TITLE_RU,
                                description_ru=RECRUIT_JOB_DESCRIPTION_RU.format(position=extra_data.get('position')))

    elif notification_type == NOTIFICATION_TYPE_GET_JOB_TYPE:
        notification_str = dict(title=GET_JOB_TITLE,
                                description=GET_JOB_DESCRIPTION.format(position=extra_data.get('position')),
                                title_ru=GET_JOB_TITLE_RU,
                                description_ru=GET_JOB_DESCRIPTION.format(position=extra_data.get('position')))

    elif notification_type == NOTIFICATION_TYPE_CHANGE_JOB_POSITION:
        notification_str = dict(title=CHANGE_JOB_POSITION_TITLE,
                                description=CHANGE_JOB_POSITION_DESCRIPTION.format(
                                    old_position=extra_data.get('old_position'),
                                    new_position=extra_data.get('new_position')),
                                title_ru=CHANGE_JOB_POSITION_TITLE_RU,
                                description_ru=CHANGE_JOB_POSITION_DESCRIPTION_RU.format(
                                    old_position=extra_data.get('old_position'),
                                    new_position=extra_data.get('new_position'))
                                )
    elif notification_type == NOTIFICATION_TYPE_DISMISS_JOB:
        notification_str = dict(title=DISMISS_JOB_TITLE,
                                description=DISMISS_JOB_DESCRIPTION.format(position=extra_data.get('position')),
                                title_ru=DISMISS_JOB_TITLE_RU,
                                description_ru=DISMISS_JOB_DESCRIPTION_RU.format(position=extra_data.get('position')),
                                )

    elif notification_type == NOTIFICATION_TYPE_QUIT_JOB:
        notification_str = dict(title=QUIT_JOB_TITLE,
                                description=QUIT_JOB_DESCRIPTION.format(position=extra_data.get('position')),
                                title_ru=QUIT_JOB_TITLE_RU,
                                description_ru=QUIT_JOB_DESCRIPTION_RU.format(position=extra_data.get('position')),
                                )

    elif notification_type == NOTIFICATION_TYPE_CHANGE_JOB_POSITION_OWNER:
        notification_str = dict(title=CHANGE_JOB_POSITION_OWNER_TITLE,
                                description=CHANGE_JOB_POSITION_OWNER_DESCRIPTION.format(
                                    old_position=extra_data.get('old_position'),
                                    new_position=extra_data.get('new_position')),
                                title_ru=CHANGE_JOB_POSITION_OWNER_TITLE_RU,
                                description_ru=CHANGE_JOB_POSITION_OWNER_DESCRIPTION_RU.format(
                                    old_position=extra_data.get('old_position'),
                                    new_position=extra_data.get('new_position')),
                                )
    elif notification_type == NOTIFICATION_TYPE_ACCEPT_PARTNERSHIP_RECIPIENT_TYPE:
        notification_str = dict(
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data.get('sender_organization'),
                                                   recipient_organization=extra_data.get('recipient_organization')),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data.get('address')),
            title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data.get('sender_organization'),
                                                         recipient_organization=extra_data.get(
                                                             'recipient_organization')),
            description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data.get('address')))

    elif notification_type == NOTIFICATION_TYPE_DECLINE_PARTNERSHIP_RECIPIENT_TYPE:
        notification_str = dict(
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data.get('sender_organization'),
                                                   recipient_organization=extra_data.get('recipient_organization')),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data.get('address')),
            title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data.get('sender_organization'),
                                                         recipient_organization=extra_data.get(
                                                             'recipient_organization')),
            description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data.get('address')))

    elif notification_type == NOTIFICATION_TYPE_REQUEST_PARTNERSHIP_RECIPIENT_TYPE:
        notification_str = dict(
            title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data.get('sender_organization'),
                                                   recipient_organization=extra_data.get('recipient_organization')),
            description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data.get('address')),
            title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data.get('sender_organization'),
                                                         recipient_organization=extra_data.get(
                                                             'recipient_organization')),
            description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data.get('address')))

    elif notification_type == ACCEPT_ORDER_TYPE:
        notification_str = dict(
            title=ACCEPT_ORDER_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=ORDER_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_ORDER_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=ORDER_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')),
            currency=extra_data.get('currency'))

    elif notification_type == ACCEPT_RENTAL_TYPE:
        notification_str = dict(
            title=ACCEPT_RENTAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_RENTAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')),
            currency=extra_data.get('currency'))

    elif notification_type == DECLINE_ORDER_TYPE:
        notification_str = dict(
            title=DECLINE_ORDER_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=ORDER_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_ORDER_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=ORDER_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_RENTAL_TYPE:
        notification_str = dict(
            title=DECLINE_RENTAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_RENTAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ACCEPT_ORDER_PAYMENT_TYPE:
        notification_str = dict(
            title=ACCEPT_RENTAL_PAYMENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_RENTAL_PAYMENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ACCEPT_RENTAL_PAYMENT_TYPE:
        notification_str = dict(
            title=ACCEPT_RENTAL_PAYMENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_RENTAL_PAYMENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ACCEPT_ORDER_PAYMENT_CLIENT_TYPE:
        notification_str = dict(
            title=ACCEPT_ORDER_PAYMENT_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_ORDER_PAYMENT_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ACCEPT_RENTAL_PAYMENT_CLIENT_TYPE:
        notification_str = dict(
            title=ACCEPT_RENTAL_PAYMENT_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_RENTAL_PAYMENT_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_ORDER_PAYMENT_CLIENT_TYPE:
        notification_str = dict(
            title=DECLINE_ORDER_PAYMENT_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_ORDER_PAYMENT_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_RENTAL_PAYMENT_CLIENT_TYPE:
        notification_str = dict(
            title=DECLINE_RENTAL_PAYMENT_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_RENTAL_PAYMENT_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_ORDER_PAYMENT_TYPE:
        notification_str = dict(
            title=DECLINE_ORDER_PAYMENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_ORDER_PAYMENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_RENTAL_PAYMENT_TYPE:
        notification_str = dict(
            title=DECLINE_RENTAL_PAYMENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_RENTAL_PAYMENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_ACCEPTED_RENTAL_TYPE:
        notification_str = dict(
            title=DECLINE_ACCEPTED_RENTAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_ACCEPTED_RENTAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_ACCEPTED_RENTAL_CLIENT_TYPE:
        notification_str = dict(
            title=DECLINE_ACCEPTED_RENTAL_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_ACCEPTED_RENTAL_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == NEW_COMMENT_TYPE:
        notification_str = dict(
            title=NEW_COMMENT_TITLE_EN,
            description=NEW_COMMENT_DESCRIPTION.format(comment_text=extra_data.get('comment_text')),
            title_ru=NEW_COMMENT_TITLE_RU,
            description_ru=NEW_COMMENT_DESCRIPTION.format(comment_text=extra_data.get('comment_text')))

    elif notification_type == REQUEST_ONLINE_ORDER_TYPE:
        notification_str = dict(
            title=REQUEST_ORDER_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=ORDER_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=REQUEST_ORDER_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=ORDER_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == REQUEST_ORDER_TYPE:
        notification_str = dict(
            title=REQUEST_ORDER_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=ORDER_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=REQUEST_ORDER_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=ORDER_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == REQUEST_RENTAL_TYPE:
        notification_str = dict(
            title=REQUEST_RENTAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=REQUEST_RENTAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))
    elif notification_type == REQUEST_RESUME_TYPE:
        notification_str = dict(
            title=REQUEST_RESUME_TITLE_EN.format(resume_name=extra_data.get('resume_name')),
            description=RESUME_DESCRIPTION_EN.format(salary_from=extra_data.get('salary_from'),
                                                     currency=extra_data.get('currency')),
            title_ru=REQUEST_RESUME_TITLE_RU.format(resume_name=extra_data.get('resume_name')),
            description_ru=RESUME_DESCRIPTION_RU.format(salary_from=extra_data.get('salary_from'),
                                                        currency=extra_data.get('currency')))

    elif notification_type == ACCEPT_ORDER_CLIENT_TYPE:
        notification_str = dict(
            title=ACCEPT_ORDER_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=ORDER_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_ORDER_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=ORDER_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))


    elif notification_type == ORGANIZATION_WITHDRAWAL_UNDER_REVIEW_TYPE:
        notification_str = dict(
            title=ORGANIZATION_UNDER_REVIEW_WITHDRAWAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=WITHDRAWAL_DESCRIPTION_EN.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                    currency=extra_data.get('currency')),
            title_ru=ORGANIZATION_UNDER_REVIEW_WITHDRAWAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=WITHDRAWAL_DESCRIPTION_RU.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == WITHDRAWAL_UNDER_REVIEW_TYPE:
        notification_str = dict(
            title=UNDER_REVIEW_WITHDRAWAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=WITHDRAWAL_DESCRIPTION_EN.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                    currency=extra_data.get('currency')),
            title_ru=UNDER_REVIEW_WITHDRAWAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=WITHDRAWAL_DESCRIPTION_RU.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ORGANIZATION_WITHDRAWAL_ACCEPTED_TYPE:
        notification_str = dict(
            title=ORGANIZATION_ACCEPTED_WITHDRAWAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=WITHDRAWAL_DESCRIPTION_EN.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                    currency=extra_data.get('currency')),
            title_ru=ORGANIZATION_ACCEPTED_WITHDRAWAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=WITHDRAWAL_DESCRIPTION_RU.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == WITHDRAWAL_ACCEPTED_TYPE:
        notification_str = dict(
            title=ACCEPTED_WITHDRAWAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=WITHDRAWAL_DESCRIPTION_EN.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPTED_WITHDRAWAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=WITHDRAWAL_DESCRIPTION_RU.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                       currency=extra_data.get('currency')))


    elif notification_type == ORGANIZATION_WITHDRAWAL_DECLINED_TYPE:
        notification_str = dict(
            title=ORGANIZATION_DECLINED_WITHDRAWAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=WITHDRAWAL_DESCRIPTION_EN.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                    currency=extra_data.get('currency')),
            title_ru=ORGANIZATION_DECLINED_WITHDRAWAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=WITHDRAWAL_DESCRIPTION_RU.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == WITHDRAWAL_DECLINED_TYPE:
        notification_str = dict(
            title=DECLINED_WITHDRAWAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=WITHDRAWAL_DESCRIPTION_EN.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINED_WITHDRAWAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=WITHDRAWAL_DESCRIPTION_RU.format(total_withdrawal=extra_data.get('total_withdrawal'),
                                                       currency=extra_data.get('currency')))


    elif notification_type == ACCEPTED_ONLINE_ORDER_CLIENT_TYPE:
        notification_str = dict(
            title=ACCEPT_ONLINE_ORDER_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=ORDER_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_ONLINE_ORDER_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=ORDER_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ACCEPT_RENTAL_CLIENT_TYPE:
        notification_str = dict(
            title=ACCEPT_RENTAL_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACCEPT_RENTAL_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_ORDER_CLIENT_TYPE:
        notification_str = dict(
            title=DECLINE_ORDER_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=ORDER_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_ORDER_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=ORDER_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == DECLINE_RENTAL_CLIENT_TYPE:
        notification_str = dict(
            title=DECLINE_RENTAL_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=DECLINE_RENTAL_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == REQUEST_ORDER_CLIENT_TYPE:
        notification_str = dict(
            title=REQUEST_ORDER_CLIENT_TITLE_EN,
            description=ORDER_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=REQUEST_ORDER_CLIENT_TITLE_RU,
            description_ru=ORDER_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == REQUEST_RENTAL_CLIENT_TYPE:
        notification_str = dict(
            title=REQUEST_RENTAL_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=REQUEST_RENTAL_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == REQUEST_RESUME_CLIENT_TYPE:
        notification_str = dict(
            title=REQUEST_RESUME_CLIENT_TITLE_EN.format(resume_name=extra_data.get('resume_name')),
            description=RESUME_DESCRIPTION_EN.format(salary_from=extra_data.get('salary_from'),
                                                     currency=extra_data.get('currency')),
            title_ru=REQUEST_RESUME_CLIENT_TITLE_RU.format(resume_name=extra_data.get('resume_name')),
            description_ru=RESUME_DESCRIPTION_RU.format(salary_from=extra_data.get('salary_from'),
                                                        currency=extra_data.get('currency')))

    elif notification_type == ACTIVATE_RENTAL_TYPE:
        notification_str = dict(
            title=ACTIVATE_RENTAL_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACTIVATE_RENTAL_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ACTIVATE_RENTAL_CLIENT_TYPE:
        notification_str = dict(
            title=ACTIVATE_RENTAL_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACTIVATE_RENTAL_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ACTIVATE_TICKET_TYPE:
        notification_str = dict(
            title=ACTIVATE_TICKET_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACTIVATE_TICKET_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == ACTIVATE_TICKET_CLIENT_TYPE:
        notification_str = dict(
            title=ACTIVATE_TICKET_CLIENT_TITLE_EN.format(transaction_id=extra_data.get('transaction_id')),
            description=RENTAL_DESCRIPTION_EN.format(total_price=extra_data.get('total_price'),
                                                    currency=extra_data.get('currency')),
            title_ru=ACTIVATE_TICKET_CLIENT_TITLE_RU.format(transaction_id=extra_data.get('transaction_id')),
            description_ru=RENTAL_DESCRIPTION_RU.format(total_price=extra_data.get('total_price'),
                                                       currency=extra_data.get('currency')))

    elif notification_type == NOTIFICATION_TYPE_AVAILABLE_DELIVERY:
        notification_str = dict(
            title=NOTIFICATION_DELIVERY_AVAILABLE_TITLE_EN,
            description=NOTIFICATION_DELIVERY_AVAILABLE_DESCRIPTION_EN.format(
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_DELIVERY_AVAILABLE_TITLE_RU,
            description_ru=NOTIFICATION_DELIVERY_AVAILABLE_DESCRIPTION_RU.format(
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION:
        notification_str = dict(
            title=NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION_TITLE_EN,
            description=NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION_DESCRIPTION_EN.format(
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_AVAILABLE_DELIVERY_ORGANIZATION_DESCRIPTION_RU.format(
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE:
        notification_str = dict(
            title=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_TITLE_EN,
            description=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id'),

            ),
            title_ru=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT:
        notification_str = dict(
            title=NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT_TITLE_EN,
            description=NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_SENT_TO_DELIVERY_BY_ORGANIZATION_FOR_CLIENT_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )

    elif notification_type == NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT:
        notification_str = dict(
            title=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT_TITLE_EN,
            description=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_CLIENT_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION:
        notification_str = dict(
            title=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_TITLE_EN,
            description=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_ACCEPTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE:
        notification_str = dict(
            title=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_TITLE_EN,
            description=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT:
        notification_str = dict(
            title=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT_TITLE_EN,
            description=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_CLIENT_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION:
        notification_str = dict(
            title=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_TITLE_EN,
            description=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_REJECTED_BY_DELIVERY_SERVICE_FOR_ORGANIZATION_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT:
        notification_str = dict(
            title=NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT_TITLE_EN,
            description=NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_DELIVERED_FOR_CLIENT_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )
    elif notification_type == NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION:
        notification_str = dict(
            title=NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION_TITLE_EN,
            description=NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION_DESCRIPTION_EN.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            ),
            title_ru=NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION_TITLE_RU,
            description_ru=NOTIFICATION_TYPE_DELIVERED_FOR_ORGANIZATION_DESCRIPTION_RU.format(
                # delivery_orgnanization=extra_data.get('delivery_orgnanization'),
                # organization=extra_data.get('organization'),
                # total_price=extra_data.get('total_price'),
                # currency=extra_data.get('currency'),
                # transaction_id=extra_data.get('transaction_id')
            )
        )

    return notification_str
