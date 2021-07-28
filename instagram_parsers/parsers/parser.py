from typing import Tuple
from django.utils.translation import gettext_lazy as _

from instagram_parsers.services.proxy_services import InstagramClientService


def get_posts(user_id: int, posts_count: int):
    try:
        cl = InstagramClientService.get_client()
        media_list = cl.user_medias(user_id=user_id, amount=posts_count)
        post = list()
        for media in media_list:
            data_s = list()
            dict_list = media.dict()
            if dict_list['resources']:
                for resource in dict_list['resources']:
                    if resource.get('video_url'):
                        video_url = str(resource.get('video_url'))
                    else:
                        video_url = None
                    data = dict(thumbnail_url=str(resource.get('thumbnail_url')), video_url=video_url,
                                pk=str((resource.get('pk'))))
                    data_s.append(data.copy())
            else:
                if dict_list.get('video_url'):
                    video_url = str(dict_list.get('video_url'))
                else:
                    video_url = None
                data = dict(thumbnail_url=str(dict_list.get('thumbnail_url')),
                            video_url=video_url,
                            pk=str((dict_list.get('pk'))))
                data_s.append(data.copy())
            code = dict_list.get('code')
            pk = str((dict_list.get('pk')))
            post_url = 'https://www.instagram.com/p/' + code + '/'
            post.append(
                dict(description=dict_list.get('caption_text'), created_at=dict_list.get('taken_at'),
                     post_url=post_url, pk=pk, data=data_s))
        return post
    except ConnectionError as e:
        return _("Connection Error")


def get_video_urls_from_post(post_url: str) -> Tuple[str, str]:
    cl = InstagramClientService.get_client()
    post_pk_from_url = cl.media_pk_from_url(url=post_url)
    media_info = cl.media_info(media_pk=post_pk_from_url)
    return media_info.video_url, media_info.thumbnail_url


def get_latest_posts(user_id: int):
    try:
        cl = InstagramClientService.get_client()
        media_list = cl.user_medias(user_id=user_id, amount=20)
        post = list()
        for media in media_list:
            data_s = list()
            dict_list = media.dict()
            if dict_list['resources']:
                for resource in dict_list['resources']:
                    if resource.get('video_url'):
                        video_url = str(resource.get('video_url'))
                    else:
                        video_url = None
                    data = dict(thumbnail_url=str(resource.get('thumbnail_url')), video_url=video_url,
                                pk=str((resource.get('pk'))))
                    data_s.append(data.copy())
            else:
                if dict_list.get('video_url'):
                    video_url = str(dict_list.get('video_url'))
                else:
                    video_url = None
                data = dict(thumbnail_url=str(dict_list.get('thumbnail_url')),
                            video_url=video_url,
                            pk=str((dict_list.get('pk'))))
                data_s.append(data.copy())
            code = dict_list.get('code')
            pk = str((dict_list.get('pk')))
            post_url = 'https://www.instagram.com/p/' + code + '/'
            post.append(
                dict(description=dict_list.get('caption_text'), created_at=dict_list.get('taken_at'),
                     post_url=post_url, pk=pk, data=data_s))
        return post
    except ConnectionError as e:
        return _("Connection Error")
