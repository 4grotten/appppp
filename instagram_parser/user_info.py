from instagram_parser.get_id import usernametoid
from instagrapi import Client


def get_instagram_user_info(username: str):
    settings = {"uuids": {"phone_id": "35729fff-aa1e-4d6a-b889-1710df661a34",
                          "uuid": "887b0e44-3b83-4996-af14-b517c96fee2f",
                          "client_session_id": "1b9cd485-5107-4e20-9bae-28a695998d1c",
                          "advertising_id": "3723cd4c-d370-4073-8507-1eb7dbb32699",
                          "device_id": "android-71b445d43959effc"},
                "cookies": {"csrftoken": "cM4BSEdZA3FQ6bXIKcZEZ8CPiRJxRPWP", "ds_user": "ss115test",
                            "ds_user_id": "44745007017", "mid": "X9napgABAAHAkPJXqGNLXYjl13_J", "rur": "PRN",
                            "sessionid": "44745007017%3AMBJ3TclCka5jaR%3A1",
                            "urlgen": "\"{158.181.250.169: 41750}:1kpTbP:boqWK79fxV5PWsmtzCmQdrw0xRA\""},
                "last_login": 1608112813.279875,
                "device_settings": {"app_version": "105.0.0.18.119", "android_version": 28,
                                    "android_release": "9.0", "dpi": "640dpi", "resolution": "1440x2560",
                                    "manufacturer": "samsung", "device": "SM-G965F", "model": "star2qltecs",
                                    "cpu": "samsungexynos9810", "version_code": "168361634"},
                "user_agent": "Instagram 105.0.0.18.119 Android (28/9.0; 640dpi; 1440x2560; samsung; SM-G965F; star2qltecs; samsungexynos9810; en_US; 168361634)"}
    cl = Client(settings=settings)
    user_id = usernametoid(username)
    user_info = dict(cl.user_info(user_id=user_id))
    full_name = user_info['full_name']
    profile_image = str(user_info['profile_pic_url'])
    return dict(full_name=full_name, profile_image=profile_image)
