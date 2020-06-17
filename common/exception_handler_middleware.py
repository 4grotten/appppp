from .exceptions import (
    ObjectNotFoundException, ValidationException, AuthenticationException,
    BadRequestException, NotAcceptableException, IntegrityException
)
from .responses import (
    NotFoundResponse, ValidationExceptionResponse, AuthenticationExceptionResponse,
    BadRequestResponse, NotAcceptableExceptionResponse, IntegrityExceptionResponse
)

EXCEPTION_MAPPER = {
    ObjectNotFoundException.__name__: NotFoundResponse,
    ValidationException.__name__: ValidationExceptionResponse,
    AuthenticationException.__name__: AuthenticationExceptionResponse,
    BadRequestException.__name__: BadRequestResponse,
    IntegrityException.__name__: IntegrityExceptionResponse,
    NotAcceptableException.__name__: NotAcceptableExceptionResponse,
}


class RequestExceptionHandlerMiddleware(object):

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        error_class = EXCEPTION_MAPPER.get(exception.__class__.__name__, None)

        if error_class:
            return error_class({'message': exception.message}, safe=False)
