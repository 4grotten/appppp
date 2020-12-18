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
    try:
        posts = list()
        web_api = MyClient(auto_patch=True, drop_incompat_keys=False)
        user_feed_info = web_api.user_feed(id, count=50)
        for post in user_feed_info:
            images = list()
            videos = list()
            data = post.pop('node', None)
            text = data.get('edge_media_to_caption')['edges'][0]['node']['text']
            created_at = data.get('taken_at_timestamp')
            if 'carousel_media' in data:
                post_with_carousel = data.get('carousel_media')
                i = 0
                for post_elements in post_with_carousel:
                    if i == len(post_with_carousel):
                        break
                    i = i + 1
                    if 'video_url' in post_elements:
                        video_url = post_elements.get('video_url')
                        thumbnail = post_elements.get('display_resources')[1]['src']
                        video = (dict(video_url=video_url, thumbnail=thumbnail).copy())
                        videos.append(video)
                    else:
                        image = dict(file=post_elements.get('display_resources')[0]['src'],
                                     small=post_elements.get('display_resources')[0]['src'],
                                     medium=post_elements.get('display_resources')[1]['src'],
                                     large=post_elements.get('display_resources')[2]['src'])
                        images.append(image.copy())

            else:
                if 'video_url' in data:
                    video_url = data.get('video_url')
                    thumbnail = data.get('images')['thumbnail']['url']
                    video = (dict(video_url=video_url, thumbnail=thumbnail).copy())
                    videos.append(video)
                else:
                    image = dict(file=data.get('display_resources')[0]['src'],
                                 small=data.get('display_resources')[0]['src'],
                                 medium=data.get('display_resources')[1]['src'],
                                 large=data.get('display_resources')[2]['src'])
                    images.append(image.copy())
            posts.append(
                dict(images=images, videos=videos, description=text, created_at=created_at))
        return posts
    except ConnectionError as e:
        return "Connection Error"
