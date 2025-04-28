import logging

import requests
from instagrapi import Client
from rest_framework import status
from transliterate.utils import _
from rest_framework.response import Response

from common.exceptions import ObjectNotFoundException, BadRequestException
from instagram_parsers.services.proxy_services import InstagramClientService
logger = logging.getLogger(__name__)

def get_instagram_user_info(username: str, host):
    remote_service_url = 'http://161.35.153.151:8080/bot/instagram-user-info/'
    login_device = InstagramClientService.get_login_device()
    proxy = f'http://{login_device.proxy_login}:{login_device.proxy_password}@{login_device.proxy_http_s}'
    try:
        try:
            response = requests.post(
                remote_service_url,
                json={'settings': login_device.settings,
                      'proxy': proxy,
                      'username': username
                      }
            )

            if response.status_code != 200:
                return Response(data=response.json(), status=response.status_code)

            user_info = response.json()
            logger.debug(f"Proxy: {user_info}")
            return user_info

        except requests.RequestException as e:
            return Response(data={
                'message': _('Error connecting to Instagram UserInfo service'),
                'errors': str(e)
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # response_dict = dict(cl.user_info_by_username(username=username))
        # user_info = {
        #     'user_id': response_dict['pk'],
        #     'full_name': response_dict['full_name'],
        #     'profile_image': str(response_dict['profile_pic_url']),
        # }
        # return user_info
    except:
        login_device.is_broke = True
        login_device.save()
        raise BadRequestException(_('Login device is invalid'))