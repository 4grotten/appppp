from django.test import TestCase

from common.exceptions import ObjectNotFoundException, ValidationException, AuthenticationException
from common.exception_handler_middleware import RequestExceptionHandlerMiddleware
from common.responses import NotFoundResponse, ValidationExceptionResponse, AuthenticationExceptionResponse


class RequestExceptionHandlerTest(TestCase):

    def setUp(self):
        self.request_handler = RequestExceptionHandlerMiddleware()

    def test_request_handler_process_exception_returns_not_found_response_with_object_not_found_exception(self):
        object_not_found_response = self.request_handler.process_exception(exception=ObjectNotFoundException(),
                                                                           request=None)
        self.assertEqual(object_not_found_response.__class__, NotFoundResponse)

    def test_request_handler_process_exception_returns_validation_exception_response_with_validation_exception(self):
        validation_exception_response = self.request_handler.process_exception(exception=ValidationException(),
                                                                               request=None)
        self.assertEqual(validation_exception_response.__class__, ValidationExceptionResponse)

    def test_request_handler_process_exception_returns_authentication_exception_response_with_authentication_exception(
            self):
        authentication_exception_response = self.request_handler.process_exception(exception=AuthenticationException(),
                                                                                   request=None)
        self.assertEqual(authentication_exception_response.__class__, AuthenticationExceptionResponse)
