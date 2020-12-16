from instagrapi import Client

cl = Client()


def get_instagram_user_info(username: str):
    user_info = dict(cl.user_info(123123))
    full_name = user_info['full_name']
    profile_image = user_info['profile_pic_url']
    return dict(full_name=full_name, profile_image=profile_image)


print(dict(get_instagram_user_info('yrysbeksagyndykov')))
