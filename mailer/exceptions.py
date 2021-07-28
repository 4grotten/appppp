from common.exceptions import GeneralException
from django.utils.translation import gettext_lazy as _


class EmailError(GeneralException):
    default_message = _('Email was not sent')
