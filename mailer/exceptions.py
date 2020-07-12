from common.exceptions import GeneralException


class EmailError(GeneralException):
    default_message = 'Email was not sent'