class GeneralException(Exception):
    default_message = 'Something went wrong'

    def __init__(self, message=None):
        self.message = message if message else self.default_message


class ObjectNotFoundException(GeneralException):
    default_message = 'Object Not Found'


class ValidationException(GeneralException):
    default_message = 'Validation Error'


class BadRequestException(GeneralException):
    default_message = 'Bad request!'


class AuthenticationException(GeneralException):
    default_message = 'Authentication failed'


class NotAcceptableException(GeneralException):
    default_message = 'Not acceptable'


class IntegrityException(GeneralException):
    default_message = 'Integrity Error'
