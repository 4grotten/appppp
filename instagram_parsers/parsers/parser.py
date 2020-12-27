from instagrapi import Client

from instagram_parsers.services.proxy_services import ProxyServices


def get_posts(user_id):
    try:
        settings = {'uuids': {'phone_id': '6605a3d5-a2a7-44f2-b7b1-ba05c979572b',
                              'uuid': 'c24cfd46-dac3-4135-8064-d7453ee2f5ef',
                              'client_session_id': '27624802-1d50-4bfa-ab8e-ad046199e940',
                              'advertising_id': '73967dfc-1605-4b65-9e6a-7bc710d2ee1f',
                              'device_id': 'android-9adddd55865dc2c7'},
                    'cookies': {'csrftoken': 'LwRgs1JTDTZWnOa0fetR0K3ALXXhmYHq', 'ds_user': 'apofi_z',
                                'ds_user_id': '45149694492', 'mid': 'X-MTIQABAAEzDuxYB6ZRM1JnMjaa', 'rur': 'RVA',
                                'sessionid': '45149694492%3AjIq4vOZE7WPR9m%3A6',
                                'urlgen': '"{158.181.250.169: 41750}:1ks0nv:CVG1dBvOC1K83neIbFUoipx6mi4"'},
                    'last_login': 1608717097.4080002,
                    'device_settings': {'app_version': '105.0.0.18.119', 'android_version': 28,
                                        'android_release': '9.0', 'dpi': '640dpi', 'resolution': '1440x2560',
                                        'manufacturer': 'samsung', 'device': 'SM-G965F', 'model': 'star2qltecs',
                                        'cpu': 'samsungexynos9810', 'version_code': '168361634'},
                    'user_agent': 'Instagram 105.0.0.18.119 Android (28/9.0; 640dpi; 1440x2560; samsung; SM-G965F; star2qltecs; samsungexynos9810; en_US; 168361634)'}

        proxy = ProxyServices.get_random_formed_proxy()
        if proxy is not None:
            cl = Client(settings=settings, proxy=proxy)
        else:
            cl = Client(settings=settings)
        media_list = cl.user_medias(user_id=user_id, amount=4)
        post = list()
        for media in media_list:
            data_s = list()
            dict_list = media.dict()
            if dict_list['resources']:
                for resource in dict_list['resources']:
                    data = dict(thumbnail_url=str(resource.get('thumbnail_url')), video_url=str(resource.get('video_url')),
                                pk=str((resource.get('pk'))))
                    data_s.append(data.copy())
            else:
                data = dict(thumbnail_url=str(dict_list.get('thumbnail_url')), video_url=str(dict_list.get('video_url')),
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
        return "Connection Error"


def get_latest_posts(user_id: int, latest_update: str):
    try:
        settings = {'uuids': {'phone_id': '6605a3d5-a2a7-44f2-b7b1-ba05c979572b',
                              'uuid': 'c24cfd46-dac3-4135-8064-d7453ee2f5ef',
                              'client_session_id': '27624802-1d50-4bfa-ab8e-ad046199e940',
                              'advertising_id': '73967dfc-1605-4b65-9e6a-7bc710d2ee1f',
                              'device_id': 'android-9adddd55865dc2c7'},
                    'cookies': {'csrftoken': 'LwRgs1JTDTZWnOa0fetR0K3ALXXhmYHq', 'ds_user': 'apofi_z',
                                'ds_user_id': '45149694492', 'mid': 'X-MTIQABAAEzDuxYB6ZRM1JnMjaa', 'rur': 'RVA',
                                'sessionid': '45149694492%3AjIq4vOZE7WPR9m%3A6',
                                'urlgen': '"{158.181.250.169: 41750}:1ks0nv:CVG1dBvOC1K83neIbFUoipx6mi4"'},
                    'last_login': 1608717097.4080002,
                    'device_settings': {'app_version': '105.0.0.18.119', 'android_version': 28,
                                        'android_release': '9.0', 'dpi': '640dpi', 'resolution': '1440x2560',
                                        'manufacturer': 'samsung', 'device': 'SM-G965F', 'model': 'star2qltecs',
                                        'cpu': 'samsungexynos9810', 'version_code': '168361634'},
                    'user_agent': 'Instagram 105.0.0.18.119 Android (28/9.0; 640dpi; 1440x2560; samsung; SM-G965F; star2qltecs; samsungexynos9810; en_US; 168361634)'}

        proxy = ProxyServices.get_random_formed_proxy()
        if proxy is not None:
            cl = Client(settings=settings, proxy=proxy)
        else:
            cl = Client(settings=settings)
        media_list = cl.user_medias(user_id=user_id, amount=10)
        posts = list()
        for media in media_list:
            images = list()
            videos = list()
            dict_list = media.dict()
            if dict_list['resources']:
                for resource in dict_list['resources']:
                    if resource['video_url']:
                        video_url = str(resource.get('video_url'))
                        thumbnail = str(resource.get('thumbnail_url'))
                        video = (dict(video_url=video_url, thumbnail=thumbnail).copy())
                        videos.append(video)
                    else:
                        image = dict(file=str(resource.get('thumbnail_url')),
                                     small=str(resource.get('thumbnail_url')),
                                     medium=str(resource.get('thumbnail_url')),
                                     large=str(resource.get('thumbnail_url')))
                        images.append(image.copy())
            else:
                if dict_list['video_url']:
                    video_url = str(dict_list.get('video_url'))
                    thumbnail = str(dict_list.get('thumbnail_url'))
                    video = (dict(video_url=video_url, thumbnail=thumbnail).copy())
                    videos.append(video)
                else:
                    image = dict(file=str(dict_list.get('thumbnail_url')),
                                 small=str(dict_list.get('thumbnail_url')),
                                 medium=str(dict_list.get('thumbnail_url')),
                                 large=str(dict_list.get('thumbnail_url')))
                    images.append(image.copy())
            code = dict_list.get('code')
            post_url = 'https://www.instagram.com/p/' + code + '/'
            if str(dict_list.get('taken_at')) == latest_update:
                break
            posts.append(
                dict(images=images, videos=videos, description=dict_list.get('caption_text'),
                     created_at=dict_list.get('taken_at'), post_url=post_url))
        return posts

    except ConnectionError as e:
        return "Connection Error"
