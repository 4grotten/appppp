from django.utils.translation import gettext_lazy as _


class GeneralException(Exception):
    default_message = _('Something went wrong')

    def __init__(self, message=None):
        self.message = message if message else self.default_message


class ObjectNotFoundException(GeneralException):
    default_message = _('Object Not Found')


class ValidationException(GeneralException):
    default_message = _('Validation Error')


class BadRequestException(GeneralException):
    default_message = _('Bad request!')


class AuthenticationException(GeneralException):
    default_message = _('Authentication failed')


class NotAcceptableException(GeneralException):
    default_message = _('Not acceptable')


class IntegrityException(GeneralException):
    default_message = _('Integrity Error')


class PermissionDeniedException(GeneralException):
    default_message = _('You do not have permission')
