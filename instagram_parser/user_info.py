from instagram_parser.get_id import usernametoid
from instagrapi import Client

cl = Client()


def get_instagram_user_info(username: str):
    user_id = usernametoid(username)
    user_info = dict(cl.user_info(user_id=user_id))
    full_name = user_info['full_name']
    profile_image = user_info['profile_pic_url']
    return dict(full_name=full_name, profile_image=profile_image)


print(dict(get_instagram_user_info('yrysbeksagyndykov')))
