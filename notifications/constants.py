DISCOUNT_NOTIFICATION_MODE = 'discount'
SUBSCRIPTION_NOTIFICATION_MODE = 'subscription'
SYSTEM_NOTIFICATION_MODE = 'system'
PARTNER_MODE = 'partner'
PERSONAL_MODE = 'personal'

NOTIFICATION_MODES = (
    (DISCOUNT_NOTIFICATION_MODE, DISCOUNT_NOTIFICATION_MODE.capitalize()),
    (SUBSCRIPTION_NOTIFICATION_MODE, SUBSCRIPTION_NOTIFICATION_MODE.capitalize()),
    (SYSTEM_NOTIFICATION_MODE, SYSTEM_NOTIFICATION_MODE.capitalize()),
    (PARTNER_MODE, PARTNER_MODE.capitalize()),
    (PERSONAL_MODE, PERSONAL_MODE.capitalize())
)

ACCEPT_PARTNERSHIP_TYPE = 'accepted_partnership'
DECLINE_PARTNERSHIP_TYPE = 'declined_partnership'
REQUEST_PARTNERSHIP_TYPE = 'requested_partnership'

ACCEPT_PARTNERSHIP_RECIPIENT_TYPE = 'accepted_partnership_recipient'
DECLINE_PARTNERSHIP_RECIPIENT_TYPE = 'declined_partnership_recipient'
REQUEST_PARTNERSHIP_RECIPIENT_TYPE = 'requested_partnership_recipient'

RECRUIT_JOB_TYPE = 'recruit'
GET_JOB_TYPE = 'get_job'
CHANGE_JOB_POSITION_TYPE = 'changed_position'
CHANGE_JOB_POSITION_OWNER_TYPE = 'changed_position_as_owner'
DISMISS_JOB_TYPE = 'dismissed'
QUIT_JOB_TYPE = 'quit'

ACCEPT_DISCOUNT_TYPE = 'accept_discount'
ACCEPT_SELLER_DISCOUNT_TYPE = 'accepted_seller_discount'
DECLINE_DISCOUNT_TYPE = 'decline_discount'
NEW_DISCOUNT_TYPE = 'new_discount'
NEW_ORGANIZATION = 'new_organization'
FOLLOWED_TO_ORGANIZATION_TYPE = 'followed_to_organization'
ORGANIZATION_FOLLOWED_TYPE = 'organization_followed'
SYSTEM_TYPE = 'system'
ORGANIZATION_MESSAGE_TYPE = 'organization_message'
ORGANIZATION_MESSAGE_SENDER_TYPE = 'sent_message'

ORGANIZATION_GAVE_TYPE = 'gave_organization'
ORGANIZATION_OWN_TYPE = 'owned_organization'

ATTENDANCE_IN = 'attendance_in'
ATTENDANCE_OUT = 'attendance_out'
CHECK_ATTENDANCE_IN = 'check_attendance_in'
CHECK_ATTENDANCE_OUT = 'check_attendance_out'

WITHDRAW_CASHBACK_CLIENT = 'withdraw_cashback_client'
CHARGE_CASHBACK_CLIENT = 'charge_cashback_client'

WITHDRAW_CASHBACK_SELLER = 'withdraw_cashback_seller'
CHARGE_CASHBACK_SELLER = 'charge_cashback_seller'

NOTIFICATION_TYPES = (
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
    (FOLLOWED_TO_ORGANIZATION_TYPE, FOLLOWED_TO_ORGANIZATION_TYPE),
    (ORGANIZATION_FOLLOWED_TYPE, ORGANIZATION_FOLLOWED_TYPE),
    (SYSTEM_TYPE, SYSTEM_TYPE),
    (ACCEPT_PARTNERSHIP_TYPE, ACCEPT_PARTNERSHIP_TYPE),
    (DECLINE_PARTNERSHIP_TYPE, DECLINE_PARTNERSHIP_TYPE),
    (REQUEST_PARTNERSHIP_TYPE, REQUEST_PARTNERSHIP_TYPE),
    (ACCEPT_SELLER_DISCOUNT_TYPE, ACCEPT_SELLER_DISCOUNT_TYPE),
    (RECRUIT_JOB_TYPE, RECRUIT_JOB_TYPE),
    (CHANGE_JOB_POSITION_TYPE, CHANGE_JOB_POSITION_TYPE),
    (DISMISS_JOB_TYPE, DISMISS_JOB_TYPE),
    (QUIT_JOB_TYPE, QUIT_JOB_TYPE),
    (CHANGE_JOB_POSITION_OWNER_TYPE, CHANGE_JOB_POSITION_OWNER_TYPE),
    (ORGANIZATION_MESSAGE_TYPE, ORGANIZATION_MESSAGE_TYPE),
    (ORGANIZATION_GAVE_TYPE, ORGANIZATION_GAVE_TYPE),
    (ORGANIZATION_OWN_TYPE, ORGANIZATION_OWN_TYPE),
    (ORGANIZATION_MESSAGE_SENDER_TYPE, ORGANIZATION_MESSAGE_SENDER_TYPE),
    (ACCEPT_PARTNERSHIP_RECIPIENT_TYPE, ACCEPT_PARTNERSHIP_RECIPIENT_TYPE),
    (DECLINE_PARTNERSHIP_RECIPIENT_TYPE, DECLINE_PARTNERSHIP_RECIPIENT_TYPE),
    (REQUEST_PARTNERSHIP_RECIPIENT_TYPE, REQUEST_PARTNERSHIP_RECIPIENT_TYPE)
)

# ______________________RUSSIAN___________________________#

ATTENDANCE_IN_TITLE_RU = 'Вход {organization}'
ATTENDANCE_OUT_TITLE_RU = 'Выход {organization}'
CHECK_ATTENDANCE_IN_TITLE_RU = 'Пропуск на вход {organization}'
CHECK_ATTENDANCE_OUT_TITLE_RU = 'Пропуск на выход {organization}'

ATTENDANCE_DESCRIPTION_RU = 'Пропуск:'

FOLLOWED_TO_ORGANIZATION_TITLE_RU = 'На вашу организацию подписались'
ORGANIZATION_FOLLOWED_TITLE_RU = 'Вы подписались на {org_title}'
DISCOUNT_COMPLETE_USER_TITLE_RU = 'Вам провели скидку {discount_percent} %'
DISCOUNT_COMPLETE_DESCRIPTION_RU = 'Итого со скидкой: {final_amount} {currency}'
DISCOUNT_COMPLETE_TITLE_RU = 'Вы провели скидку {discount_percent} %'

NEW_DISCOUNT_TITLE_RU = 'Доступна новая скидка {percent} %'
NEW_CASHBACK_TITLE_RU = 'Доступен новый кэшбек {percent} %'

NEW_DISCOUNT_DESCRIPTION_RU = '{address} '
PARTNERSHIP_REQUEST_TITLE_RU = '{sender_organization} хочет стать партнером {recipient_organization}'
PARTNERSHIP_REQUEST_DESCRIPTION_RU = '{address} '
SUBSCRIPTION_NOTIFICATION_DESCRIPTION_RU = '{address} '
TRANSACTION_DECLINED_NOTIFICATION_TITLE_RU = 'Вам отменили сделку'
YOU_DECLINED_NOTIFICATION_TITLE_RU = 'Вы отменили сделку'
TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION_RU = 'Скидка {savings} {currency}'

NEW_ORGANIZATION_TITLE_RU = 'Новая организация доступна для вас'
NEW_ORGANIZATION_DESCRIPTION_RU = '{organization_title} '

RECRUIT_JOB_TITLE_RU = 'Вы приняли на работу'
RECRUIT_JOB_DESCRIPTION_RU = '{position} '

GET_JOB_TITLE_RU = 'Вас приняли на работу {organization}'
GET_JOB_DESCRIPTION_RU = '{position} '

CHANGE_JOB_POSITION_TITLE_RU = 'Вас назначили на новую должность'
CHANGE_JOB_POSITION_DESCRIPTION_RU = '{old_position} на {new_position}'

CHANGE_JOB_POSITION_OWNER_TITLE_RU = 'Вы назначили другую должность'
CHANGE_JOB_POSITION_OWNER_DESCRIPTION_RU = '{old_position} на {new_position}'

QUIT_JOB_TITLE_RU = 'Вас уволили с работы {organization}'
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

ORGANIZATION_GAVE_TITLE_RU = 'Вы передали права собственника {organization}'
ORGANIZATION_GAVE_DESCRIPTION_RU = ' '

ORGANIZATION_OWN_TITLE_RU = 'Поздравляем Вы стали собственником {organization}'
ORGANIZATION_OWN_DESCRIPTION_RU = ' '

WITHDRAW_CASHBACK_CLIENT_TITLE_RU = 'Поздравляем Вам сняли {amount} {currency} с кешбэка'
CHARGE_CASHBACK_CLIENT_TITLE_RU = 'Поздравляем вам начислили кешбэк {amount} {currency}'

WITHDRAW_CASHBACK_SELLER_TITLE_RU = 'Вы сняли {amount} {currency} с кешбека'
CHARGE_CASHBACK_SELLER_TITLE_RU = 'Вы начислили кешбек {amount} {currency}'

# _______________________ ENGLISH _______________________#

ATTENDANCE_IN_TITLE = 'Input {organization}'
ATTENDANCE_OUT_TITLE = 'Exit {organization}'
CHECK_ATTENDANCE_IN_TITLE = 'Entry pass {organization}'
CHECK_ATTENDANCE_OUT_TITLE = 'Exit pass {organization}'

ATTENDANCE_DESCRIPTION = 'Pass:'

FOLLOWED_TO_ORGANIZATION_TITLE = 'subscribed on your organization'
ORGANIZATION_FOLLOWED_TITLE = 'You subscribed to {org_title}'
DISCOUNT_COMPLETE_USER_TITLE = 'You got a discount {discount_percent} %'
DISCOUNT_COMPLETE_DESCRIPTION = 'Total with discount:{final_amount} {currency}'
DISCOUNT_COMPLETE_TITLE = 'You made a discount {discount_percent} %'

NEW_DISCOUNT_TITLE = 'New discount available {percent} %'
NEW_CASHBACK_TITLE = 'New cashback available {percent} %'

NEW_DISCOUNT_DESCRIPTION = '{address} '
PARTNERSHIP_REQUEST_TITLE = '{sender_organization} wants become a partner {recipient_organization}'
PARTNERSHIP_REQUEST_DESCRIPTION = '{address} '
SUBSCRIPTION_NOTIFICATION_DESCRIPTION = '{address} '
TRANSACTION_DECLINED_NOTIFICATION_TITLE = 'Your deal was canceled'
YOU_DECLINED_NOTIFICATION_TITLE = 'You canceled the deal'
TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION = 'Discount{savings} {currency}'

NEW_ORGANIZATION_TITLE = 'New organization is available for you '
NEW_ORGANIZATION_DESCRIPTION = '{organization_title} '

RECRUIT_JOB_TITLE = 'You hired an employee'
RECRUIT_JOB_DESCRIPTION = '{position} '

GET_JOB_TITLE = 'You were hired as an employee {organization}'
GET_JOB_DESCRIPTION = '{position} '

CHANGE_JOB_POSITION_TITLE = 'You have been appointed to new position'
CHANGE_JOB_POSITION_DESCRIPTION = '{old_position} на {new_position}'

CHANGE_JOB_POSITION_OWNER_TITLE = 'You have appointed different position'
CHANGE_JOB_POSITION_OWNER_DESCRIPTION = '{old_position} to {new_position}'

QUIT_JOB_TITLE = 'You got fired from {organization}'
QUIT_JOB_DESCRIPTION = '{position} '

DISMISS_JOB_TITLE = 'You got fired from'
DISMISS_JOB_DESCRIPTION = '{position} '

ORGANIZATION_MESSAGE_TITLE = 'Message from '
ORGANIZATION_MESSAGE_PARTNERS_TITLE = 'Message for partners'
ORGANIZATION_MESSAGE_PARTNERS_FOLLOWERS_TITLE = 'Message to subscribers of partners'
ORGANIZATION_MESSAGE_DESCRIPTION = '{content} '
ORGANIZATION_OWNER_MESSAGE_TITLE = 'You have sent a message'
ORGANIZATION_OWNER_MESSAGE_PARTNERS_TITLE = 'You have sent a message to partners'
ORGANIZATION_OWNER_MESSAGE_PARTNERS_FOLLOWERS_TITLE = 'You have sent message to your partners subscribers'

ORGANIZATION_GAVE_TITLE = 'You have transferred ownership rights {organization}'
ORGANIZATION_GAVE_DESCRIPTION = ' '

ORGANIZATION_OWN_TITLE = 'Congratulations, you become owner {organization}'
ORGANIZATION_OWN_DESCRIPTION = ' '

WITHDRAW_CASHBACK_CLIENT_TITLE = 'Congratulations you have paid,{amount} {currency} from cashback'
CHARGE_CASHBACK_CLIENT_TITLE = ' Congratulations you received cashback {amount} {currency}'

WITHDRAW_CASHBACK_SELLER_TITLE = 'You took transfer{amount} {currency} from cashback '
CHARGE_CASHBACK_SELLER_TITLE = 'You have credited cashback {amount} {currency}'


def get_titles_descriptions_from_type(notification_type: str, extra_data=None) -> dict:
    notification_str = dict()

    if notification_type == NEW_ORGANIZATION:
        notification_str = dict(title=NEW_ORGANIZATION_TITLE,
                                description=NEW_ORGANIZATION_DESCRIPTION.format(
                                    organization_title=extra_data['organization_title']),
                                title_ru=NEW_ORGANIZATION_TITLE_RU,
                                description_ru=NEW_ORGANIZATION_DESCRIPTION_RU.format(
                                    organization_title=extra_data['organization_title']))

    elif notification_type == ORGANIZATION_OWN_TYPE:
        notification_str = dict(title=ORGANIZATION_OWN_TITLE.format(organization=extra_data['organization']),
                                description=ORGANIZATION_OWN_DESCRIPTION,
                                title_ru=ORGANIZATION_OWN_TITLE_RU,
                                description_ru=ORGANIZATION_OWN_DESCRIPTION)

    elif notification_type == ORGANIZATION_GAVE_TYPE:
        notification_str = dict(title=ORGANIZATION_GAVE_TITLE.format(organization=extra_data['organization']),
                                description=ORGANIZATION_GAVE_DESCRIPTION,
                                title_ru=ORGANIZATION_GAVE_TITLE_RU.format(organization=extra_data['organization']),
                                description_ru=ORGANIZATION_GAVE_DESCRIPTION)

    elif notification_type == ORGANIZATION_MESSAGE_TYPE:
        title_ru = ''
        title = ''
        if extra_data['message_to'] == 'organization_followers':
            title = ORGANIZATION_MESSAGE_TITLE
            title_ru = ORGANIZATION_MESSAGE_TITLE_RU
        elif extra_data['message_to'] == 'partners_followers':
            title = ORGANIZATION_MESSAGE_PARTNERS_FOLLOWERS_TITLE
            title_ru = ORGANIZATION_MESSAGE_PARTNERS_FOLLOWERS_TITLE_RU
        elif extra_data['message_to'] == 'partners_members':
            title = ORGANIZATION_MESSAGE_PARTNERS_TITLE
            title_ru = ORGANIZATION_MESSAGE_PARTNERS_TITLE_RU
        notification_str = dict(title=title,
                                description=ORGANIZATION_MESSAGE_DESCRIPTION.format(content=extra_data['content']),
                                title_ru=title_ru,
                                description_ru=ORGANIZATION_MESSAGE_DESCRIPTION_RU.format(
                                    content=extra_data['content']))
    elif notification_type == ORGANIZATION_MESSAGE_SENDER_TYPE:
        title_ru = ''
        title = ''
        if extra_data['message_to'] == 'organization_followers':
            title = ORGANIZATION_OWNER_MESSAGE_TITLE
            title_ru = ORGANIZATION_OWNER_MESSAGE_TITLE_RU
        elif extra_data['message_to'] == 'partners_followers':
            title = ORGANIZATION_OWNER_MESSAGE_PARTNERS_FOLLOWERS_TITLE
            title_ru = ORGANIZATION_OWNER_MESSAGE_PARTNERS_FOLLOWERS_TITLE_RU
        elif extra_data['message_to'] == 'partners_members':
            title = ORGANIZATION_OWNER_MESSAGE_PARTNERS_TITLE
            title_ru = ORGANIZATION_OWNER_MESSAGE_PARTNERS_TITLE_RU
        notification_str = dict(title=title,
                                description=ORGANIZATION_MESSAGE_DESCRIPTION.format(content=extra_data['content']),
                                title_ru=title_ru,
                                description_ru=ORGANIZATION_MESSAGE_DESCRIPTION_RU.format(
                                    content=extra_data['content']))
    elif notification_type == NEW_DISCOUNT_TYPE:
        title = ''
        title_ru = ''
        if extra_data['percent']:
            title = NEW_DISCOUNT_TITLE.format(percent=extra_data['percent'])
            title_ru = NEW_DISCOUNT_TITLE_RU.format(percent=extra_data['percent'])
        elif extra_data['cashback']:
            title = NEW_CASHBACK_TITLE.format(percent=extra_data['cashback'])
            title_ru = NEW_CASHBACK_TITLE_RU.format(percent=extra_data['cashback'])
        notification_str = dict(title=title,
                                description=NEW_DISCOUNT_DESCRIPTION.format(address=extra_data['address']),
                                title_ru=title_ru,
                                description_ru=NEW_DISCOUNT_DESCRIPTION_RU.format(address=extra_data['address']))

    elif notification_type == WITHDRAW_CASHBACK_CLIENT:
        notification_str = dict(
            title=WITHDRAW_CASHBACK_CLIENT_TITLE.format(amount=extra_data['amount'], currency=extra_data['currency']),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data['final_amount'],
                                                             currency=extra_data['currency']),
            title_ru=WITHDRAW_CASHBACK_CLIENT_TITLE_RU.format(amount=extra_data['amount'],
                                                              currency=extra_data['currency']),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data['final_amount'],
                                                                   currency=extra_data['currency']))
    elif notification_type == CHARGE_CASHBACK_CLIENT:
        notification_str = dict(
            title=CHARGE_CASHBACK_CLIENT_TITLE.format(amount=extra_data['amount'], currency=extra_data['currency']),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data['final_amount'],
                                                             currency=extra_data['currency']),
            title_ru=CHARGE_CASHBACK_CLIENT_TITLE_RU.format(amount=extra_data['amount'],
                                                            currency=extra_data['currency']),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data['final_amount'],
                                                                   currency=extra_data['currency']))
    elif notification_type == WITHDRAW_CASHBACK_SELLER:
        notification_str = dict(
            title=WITHDRAW_CASHBACK_SELLER_TITLE.format(amount=extra_data['amount'], currency=extra_data['currency']),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data['final_amount'],
                                                             currency=extra_data['currency']),
            title_ru=WITHDRAW_CASHBACK_SELLER_TITLE_RU.format(amount=extra_data['amount'],
                                                              currency=extra_data['currency']),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data['final_amount'],
                                                                   currency=extra_data['currency']))
    elif notification_type == CHARGE_CASHBACK_SELLER:
        notification_str = dict(
            title=CHARGE_CASHBACK_SELLER_TITLE.format(amount=extra_data['amount'], currency=extra_data['currency']),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data['final_amount'],
                                                             currency=extra_data['currency']),
            title_ru=CHARGE_CASHBACK_SELLER_TITLE_RU.format(amount=extra_data['amount'],
                                                            currency=extra_data['currency']),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data['final_amount'],
                                                                   currency=extra_data['currency']))
    elif notification_type == CHECK_ATTENDANCE_IN:
        dict(title=CHECK_ATTENDANCE_IN_TITLE.format(organization=extra_data['organization']),
             description=ATTENDANCE_DESCRIPTION,
             title_ru=CHECK_ATTENDANCE_IN_TITLE_RU.format(organization=extra_data['organization']),
             description_ru=ATTENDANCE_DESCRIPTION_RU)

    elif notification_type == CHECK_ATTENDANCE_OUT:
        dict(title=CHECK_ATTENDANCE_OUT_TITLE.format(organization=extra_data['organization']),
             description=ATTENDANCE_DESCRIPTION,
             title_ru=CHECK_ATTENDANCE_OUT_TITLE_RU.format(organization=extra_data['organization']),
             description_ru=ATTENDANCE_DESCRIPTION_RU)

    elif notification_type == ATTENDANCE_IN:
        dict(title=ATTENDANCE_IN_TITLE.format(organization=extra_data['organization']),
             description=ATTENDANCE_DESCRIPTION,
             title_ru=ATTENDANCE_IN_TITLE_RU.format(organization=extra_data['organization']),
             description_ru=ATTENDANCE_DESCRIPTION_RU)

    elif notification_type == ATTENDANCE_OUT:
        dict(title=ATTENDANCE_OUT_TITLE.format(organization=extra_data['organization']),
             description=ATTENDANCE_DESCRIPTION,
             title_ru=ATTENDANCE_OUT_TITLE_RU.format(organization=extra_data['organization']),
             description_ru=ATTENDANCE_DESCRIPTION_RU)

    elif notification_type == ACCEPT_DISCOUNT_TYPE:
        notification_str = dict(
            title=DISCOUNT_COMPLETE_USER_TITLE.format(discount_percent=extra_data['discount_percent']),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data['final_amount'],
                                                             currency=extra_data['currency']),
            title_ru=DISCOUNT_COMPLETE_USER_TITLE_RU.format(discount_percent=extra_data['discount_percent']),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data['final_amount'],
                                                                   currency=extra_data['currency']))


    elif notification_type == ACCEPT_SELLER_DISCOUNT_TYPE:
        notification_str = dict(
            title=DISCOUNT_COMPLETE_TITLE.format(discount_percent=extra_data['discount_percent']),
            description=DISCOUNT_COMPLETE_DESCRIPTION.format(final_amount=extra_data['final_amount'],
                                                             currency=extra_data['currency']),
            title_ru=DISCOUNT_COMPLETE_USER_TITLE_RU.format(discount_percent=extra_data['discount_percent']),
            description_ru=DISCOUNT_COMPLETE_DESCRIPTION_RU.format(final_amount=extra_data['final_amount'],
                                                                   currency=extra_data['currency']))

    elif notification_type == DECLINE_DISCOUNT_TYPE:

        if extra_data['recipient'] == 'client':
            notification_str = dict(
                title=TRANSACTION_DECLINED_NOTIFICATION_TITLE,
                description=TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION.format(savings=extra_data['savings'],
                                                                                 currency=extra_data['currency']),
                title_ru=TRANSACTION_DECLINED_NOTIFICATION_TITLE_RU,
                description_ru=TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION.format(savings=extra_data['savings'],
                                                                                    currency=extra_data['currency']))
        else:
            notification_str = dict(
                title=YOU_DECLINED_NOTIFICATION_TITLE,
                description=TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION.format(savings=extra_data['savings'],
                                                                                 currency=extra_data['currency']),
                title_ru=YOU_DECLINED_NOTIFICATION_TITLE_RU,
                description_ru=TRANSACTION_DECLINED_NOTIFICATION_DESCRIPTION.format(savings=extra_data['savings'],
                                                                                    currency=extra_data['currency']))

    elif notification_type == FOLLOWED_TO_ORGANIZATION_TYPE:
        dict(title=FOLLOWED_TO_ORGANIZATION_TITLE,
             description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=extra_data['address']),
             title_ru=FOLLOWED_TO_ORGANIZATION_TITLE_RU,
             description_ru=SUBSCRIPTION_NOTIFICATION_DESCRIPTION_RU.format(address=extra_data['address']))

    elif notification_type == ORGANIZATION_FOLLOWED_TYPE:
        dict(title=ORGANIZATION_FOLLOWED_TITLE.format(org_title=extra_data['org_title']),
             description=SUBSCRIPTION_NOTIFICATION_DESCRIPTION.format(address=extra_data['address']),
             title_ru=ORGANIZATION_FOLLOWED_TITLE_RU.format(org_title=extra_data['org_title']),
             description_ru=SUBSCRIPTION_NOTIFICATION_DESCRIPTION_RU.format(address=extra_data['address']))

    elif notification_type == ACCEPT_PARTNERSHIP_TYPE:
        dict(title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data['sender_organization'],
                                                    recipient_organization=extra_data['recipient_organization']),
             description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data['address']),
             title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data['sender_organization'],
                                                          recipient_organization=extra_data['recipient_organization']),
             description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data['address']))

    elif notification_type == DECLINE_PARTNERSHIP_TYPE:
        dict(title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data['sender_organization'],
                                                    recipient_organization=extra_data['recipient_organization']),
             description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data['address']),
             title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data['sender_organization'],
                                                          recipient_organization=extra_data['recipient_organization']),
             description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data['address']))

    elif notification_type == REQUEST_PARTNERSHIP_TYPE:
        dict(title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data['sender_organization'],
                                                    recipient_organization=extra_data['recipient_organization']),
             description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data['address']),
             title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data['sender_organization'],
                                                          recipient_organization=extra_data['recipient_organization']),
             description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data['address']))

    elif notification_type == RECRUIT_JOB_TYPE:
        dict(title=RECRUIT_JOB_TITLE,
             description=RECRUIT_JOB_DESCRIPTION.format(position=extra_data['position']),
             title_ru=RECRUIT_JOB_TITLE_RU,
             description_ru=RECRUIT_JOB_DESCRIPTION_RU.format(position=extra_data['position']))

    elif notification_type == CHANGE_JOB_POSITION_TYPE:
        dict(title=CHANGE_JOB_POSITION_TITLE,
             description=CHANGE_JOB_POSITION_DESCRIPTION.format(old_position=extra_data['old_position'],
                                                                new_position=extra_data['new_position']),
             title_ru=CHANGE_JOB_POSITION_TITLE_RU,
             description_ru=CHANGE_JOB_POSITION_DESCRIPTION_RU.format(old_position=extra_data['old_position'],
                                                                      new_position=extra_data['new_position'])
             )
    elif notification_type == DISMISS_JOB_TYPE:
        dict(title=DISMISS_JOB_TITLE,
             description=DISMISS_JOB_DESCRIPTION.format(position=extra_data['position']),
             title_ru=DISMISS_JOB_TITLE_RU,
             description_ru=DISMISS_JOB_DESCRIPTION_RU.format(position=extra_data['position']),
             )

    elif notification_type == QUIT_JOB_TYPE:
        dict(title=QUIT_JOB_TITLE.format(organization=extra_data['organization']),
             description=QUIT_JOB_DESCRIPTION.format(position=extra_data['position']),
             title_ru=QUIT_JOB_TITLE_RU.format(organization=extra_data['organization']),
             description_ru=QUIT_JOB_DESCRIPTION_RU.format(position=extra_data['position']),
             )

    elif notification_type == CHANGE_JOB_POSITION_OWNER_TYPE:
        dict(title=CHANGE_JOB_POSITION_OWNER_TITLE,
             description=CHANGE_JOB_POSITION_OWNER_DESCRIPTION.format(old_position=extra_data['old_position'],
                                                                      new_position=extra_data['new_position']),
             title_ru=CHANGE_JOB_POSITION_OWNER_TITLE_RU,
             description_ru=CHANGE_JOB_POSITION_OWNER_DESCRIPTION_RU.format(old_position=extra_data['old_position'],
                                                                            new_position=extra_data['new_position']),
             )
    elif notification_type == ACCEPT_PARTNERSHIP_RECIPIENT_TYPE:
        dict(title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data['sender_organization'],
                                                    recipient_organization=extra_data['recipient_organization']),
             description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data['address']),
             title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data['sender_organization'],
                                                          recipient_organization=extra_data['recipient_organization']),
             description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data['address']))

    elif notification_type == DECLINE_PARTNERSHIP_RECIPIENT_TYPE:
        dict(title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data['sender_organization'],
                                                    recipient_organization=extra_data['recipient_organization']),
             description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data['address']),
             title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data['sender_organization'],
                                                          recipient_organization=extra_data['recipient_organization']),
             description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data['address']))

    elif notification_type == REQUEST_PARTNERSHIP_RECIPIENT_TYPE:
        dict(title=PARTNERSHIP_REQUEST_TITLE.format(sender_organization=extra_data['sender_organization'],
                                                    recipient_organization=extra_data['recipient_organization']),
             description=PARTNERSHIP_REQUEST_DESCRIPTION.format(address=extra_data['address']),
             title_ru=PARTNERSHIP_REQUEST_TITLE_RU.format(sender_organization=extra_data['sender_organization'],
                                                          recipient_organization=extra_data['recipient_organization']),
             description_ru=PARTNERSHIP_REQUEST_DESCRIPTION_RU.format(address=extra_data['address']))
    return notification_str
