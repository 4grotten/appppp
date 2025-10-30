from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import APIException
from rest_framework import status


class GeneralException(Exception):
    default_message = _("Something went wrong")

    def __init__(self, message=None):
        self.message = message if message else self.default_message


class ObjectNotFoundException(GeneralException):
    default_message = _("Object Not Found")


class ValidationException(GeneralException):
    default_message = _("Validation Error")


class BadRequestException(GeneralException):
    default_message = _("Bad request!")


class AuthenticationException(GeneralException):
    default_message = _("Authentication failed")


class NotAcceptableException(GeneralException):
    default_message = _("Not acceptable")


class IntegrityException(GeneralException):
    default_message = _("Integrity Error")


class PermissionDeniedException(GeneralException):
    default_message = _("You do not have permission")


class StockException(GeneralException):
    default_message = _("Stock error")


class CouponException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        "message": _("Please enter organization id"),
        "detail": _("Please enter organization id"),
        "code": "A1",
    }


class SubcategoryExist(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        "message": _("This subcategory already exists"),
        "detail": _("Please make sure that subcategory with this name not exists"),
        "code": "A2",
    }


class InvoiceInfoDoesNotExists(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = {
        "message": _("Invoice info for this country does not exists"),
        "detail": _("Please make sure that invoice info for this country exists"),
        "code": "A3",
    }
