from transliterate.utils import _

from common.exceptions import ObjectNotFoundException, BadRequestException
from instagram_parsers.services.proxy_services import InstagramClientService


def get_instagram_user_info(username: str):
    cl, login_device = InstagramClientService.get_client()
    try:
        response_dict = dict(cl.user_info_by_username(username=username))
        user_info = {
            'user_id': response_dict['pk'],
            'full_name': response_dict['full_name'],
            'profile_image': str(response_dict['profile_pic_url']),
        }
        return user_info
    except:
        login_device.is_broke = True
        login_device.save()
        raise BadRequestException(_('Login device is invalid'))
