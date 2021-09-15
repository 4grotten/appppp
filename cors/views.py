import requests
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram_parsers.services.proxy_services import ProxyService


class CorsView(APIView):

    def get(self, request):
        insta_url = request.META['QUERY_STRING'].replace('url=', '')
        if insta_url is None or insta_url == '':
            return Response(
                data={
                    "Error": _("Media url is not provided"),
                    }, status=status.HTTP_400_BAD_REQUEST
                )
        proxy = ProxyService.get_random_proxy_for_requests()
        if not proxy:
            proxy = []
        try:
            response = requests.get(insta_url, stream=True, proxies=proxy[0])
            response.headers.pop('cross-origin-resource-policy', None)
            answer = HttpResponse(response)
            answer.status_code = response.status_code
            for key, value in response.headers.items():
                if key == 'Connection':
                    continue
                answer[key] = value
            # return  answer
            return response.content, response.status_code, response.headers.items()
        except Exception as e:
            return Response(data={f"Error": f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
