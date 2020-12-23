from instagrapi import Client


def get_posts(user_id):
    try:
        settings = {'uuids': {'phone_id': 'cbe2558f-6488-462d-a9da-e069d84c7d97',
                              'uuid': '018dcf3b-a7fb-40ef-8f47-082c43eb1e77',
                              'client_session_id': '595c2fdc-4337-4617-acff-587b5e98ead9',
                              'advertising_id': '3a39e79a-c079-4106-9f94-3dfb4b216b9e',
                              'device_id': 'android-0fb569bd35d44c9f'},
                    'cookies': {'csrftoken': 'AbfdhBzdUvgrPspHp7OIQMBKW1nXWIuk', 'ds_user': 'apofiz.test',
                                'ds_user_id': '44841168607', 'mid': 'X-L23wABAAE6qERU8jcy95_wrjPB', 'rur': 'ASH',
                                'sessionid': '44841168607%3AxmZxf4IjgpXSS4%3A4',
                                'urlgen': '"{212.112.119.146: 12764}:1kryvI:aYjqVptuXjMk8OALZh2zWpzvG8c"'},
                    'last_login': 1608709870.392346,
                    'device_settings': {'app_version': '105.0.0.18.119', 'android_version': 28,
                                        'android_release': '9.0', 'dpi': '640dpi', 'resolution': '1440x2560',
                                        'manufacturer': 'samsung', 'device': 'SM-G965F', 'model': 'star2qltecs',
                                        'cpu': 'samsungexynos9810', 'version_code': '168361634'},
                    'user_agent': 'Instagram 105.0.0.18.119 Android (28/9.0; 640dpi; 1440x2560; samsung; SM-G965F; star2qltecs; samsungexynos9810; en_US; 168361634)'}

        cl = Client(settings=settings)

        media_list = cl.user_medias(user_id=user_id, amount=50)
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
            posts.append(
                dict(images=images, videos=videos, description=dict_list.get('caption_text'),
                     created_at=dict_list.get('taken_at'), post_url=post_url))
        return posts

    except ConnectionError as e:
        return "Connection Error"


def get_latest_posts(user_id: int, latest_update: str):
    try:
        settings = {'uuids': {'phone_id': 'cbe2558f-6488-462d-a9da-e069d84c7d97',
                              'uuid': '018dcf3b-a7fb-40ef-8f47-082c43eb1e77',
                              'client_session_id': '595c2fdc-4337-4617-acff-587b5e98ead9',
                              'advertising_id': '3a39e79a-c079-4106-9f94-3dfb4b216b9e',
                              'device_id': 'android-0fb569bd35d44c9f'},
                    'cookies': {'csrftoken': 'AbfdhBzdUvgrPspHp7OIQMBKW1nXWIuk', 'ds_user': 'apofiz.test',
                                'ds_user_id': '44841168607', 'mid': 'X-L23wABAAE6qERU8jcy95_wrjPB', 'rur': 'ASH',
                                'sessionid': '44841168607%3AxmZxf4IjgpXSS4%3A4',
                                'urlgen': '"{212.112.119.146: 12764}:1kryvI:aYjqVptuXjMk8OALZh2zWpzvG8c"'},
                    'last_login': 1608709870.392346,
                    'device_settings': {'app_version': '105.0.0.18.119', 'android_version': 28,
                                        'android_release': '9.0', 'dpi': '640dpi', 'resolution': '1440x2560',
                                        'manufacturer': 'samsung', 'device': 'SM-G965F', 'model': 'star2qltecs',
                                        'cpu': 'samsungexynos9810', 'version_code': '168361634'},
                    'user_agent': 'Instagram 105.0.0.18.119 Android (28/9.0; 640dpi; 1440x2560; samsung; SM-G965F; star2qltecs; samsungexynos9810; en_US; 168361634)'}

        cl = Client(settings=settings)
        media_list = cl.user_medias(user_id=user_id, amount=50)
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
