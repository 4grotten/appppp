from django.http import JsonResponse


class NotFoundResponse(JsonResponse):
    status_code = 404


class ValidationExceptionResponse(JsonResponse):
    status_code = 422


class BadRequestResponse(JsonResponse):
    status_code = 400


class AuthenticationExceptionResponse(JsonResponse):
    status_code = 401


class PermissionExceptionResponse(JsonResponse):
    status_code = 403


class SuccessResponse(JsonResponse):
    status_code = 200


class SuccessCreationResponse(JsonResponse):
    status_code = 201


class NotAcceptableExceptionResponse(JsonResponse):
    status_code = 406


class IntegrityExceptionResponse(JsonResponse):
    status_code = 400
