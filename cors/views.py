import json
from ipware import get_client_ip

import requests
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram_parsers.services.proxy_services import ProxyService


class CorsView(View):

    def get(self, request):
        hop_by_hop = ['Connection', 'Keep-Alive', 'Proxy-Authenticate',
                      'Proxy-Authorization', 'TE', 'Trailers', 'Transfer-Encoding', 'Upgrade']

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
            answer = HttpResponse(response.content)
            answer.status_code = response.status_code
            for key, value in response.headers.items():
                if key in hop_by_hop:
                    continue
                answer[key] = value
            return answer
        except Exception as e:
            return Response(data={f"Error": f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class IpLocation(APIView):

    def get(self, request):
        try:
            i, r = get_client_ip(request, request_header_order=['X_FORWARDED_FOR', 'REMOTE_ADDR'])
            # print('IIIII', i)

            response = requests.get('https://geolocation-db.com/jsonp/' + f'{i}')

            result = response.content.decode()
            result = result.split("(")[1].strip(")")
            result = json.loads(result)
            # print(result)

            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({f"Error": f"{str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
