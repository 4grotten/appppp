import os
from django.utils.deprecation import MiddlewareMixin


class BackendVersionHeaderMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        version = os.getenv('BACKEND_VERSION_REPORT')
        if version:
            response['X-Server-Version'] = version
        return response
