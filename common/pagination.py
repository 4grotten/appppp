from rest_framework import pagination
from rest_framework.response import Response


class GeneralPagination(pagination.PageNumberPagination):
    page_size_query_param = 'limit'
    page_query_param = 'page'

    def get_paginated_response(self, data):
        return Response({
            'total_count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'list': data
        })
