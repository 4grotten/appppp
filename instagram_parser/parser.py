import hashlib
import string
import random
from instagram_web_api import Client, ClientError, ClientLoginError  # ClientCompatPatch,
from instagram_parser import get_id
import json


# new class
class MyClient(Client):
    """_docstring_"""

    @staticmethod
    def _extract_rhx_gis(html):
        options = string.ascii_lowercase + string.digits
        text = ''.join([random.choice(options) for _ in range(8)])
        return hashlib.md5(text.encode()).hexdigest()


def get_posts(id):
    posts = list()
    try:
        web_api = MyClient(auto_patch=True, drop_incompat_keys=False)
        user_feed_info = web_api.user_feed(id, count=50)
        for post in user_feed_info:
            data = post.pop('node', None)
            url = data.get('display_url')
            text = data.get('edge_media_to_caption')['edges'][0]['node']['text']
            image = dict(
                image=dict(file=data.get('display_resources')[0]['src'], small=data.get('display_resources')[0]['src'],
                           medium=data.get('display_resources')[1]['src'],
                           large=data.get('display_resources')[2]['src']))
            thumbnail = data.get('thumbnail_src')
            created_at = data.get('taken_at_timestamp')
            if 'video_url' in data:
                is_video = data.get('is_video')
                video_url = data.get('video_url')
            else:
                is_video = False
                video_url = None
            images = list()
            videos = list()
            video = (dict(video=dict(video_url=video_url, thumbnail=thumbnail).copy()))
            images.append(image.copy())
            videos.append(video)
            posts.append(
                dict(images=images, videos=videos, description=text, created_at=created_at, is_video=is_video, ))
        return posts
    except ConnectionError as e:
        return "Connection Error"
