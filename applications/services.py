from typing import Optional, List

from django.db import transaction

from applications.models import UserApp, UserAppBanner, UserAppType
from common.exceptions import ObjectNotFoundException
from django.utils.translation import gettext_lazy as _

from common.models import File
from users.models import User


class UserAppService:
    model = UserApp

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def get(cls, *args, **kwargs) -> UserApp:
        try:
            return cls.model.objects.get(*args, **kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('UserApp not found'))

    @classmethod
    @transaction.atomic
    def create_application(cls, owner: User, title: str, description: Optional[str], image_id: File,
                           selected_banner_file_id: Optional[File] = None,
                           types: Optional[List[UserAppType]] = None,
                           banners_image_ids: Optional[List[File]] = None,
                           app_images: Optional[List[File]] = None,
                           app_link: str = '',
                           price: Optional[float] = None,
                           instagram_link: Optional[str] = None,
                           youtube_links: Optional[List[str]] = None,
                           support_link: Optional[str] = None,
                           company_link: Optional[str] = None,
                           terms_link: Optional[str] = None
                           ) -> UserApp:
        user_app = UserApp.objects.create(
            owner=owner,
            title=title,
            description=description,
            image=image_id,
            app_link=app_link,
            price=price,
            instagram_link=instagram_link,
            youtube_links=youtube_links,
            support_link=support_link,
            company_link=company_link,
            terms_link=terms_link
        )
        if types:
            user_app.types.set(types)

        if banners_image_ids is not None:
            banners = UserAppBannerService.create_banners(banners_image_ids)
            user_app.banners.set(banners)
            selected_banner_file = selected_banner_file_id
            selected_banner = next((b for b in banners if b.image == selected_banner_file), None)
            if selected_banner:
                user_app.selected_banner = selected_banner
                user_app.save()
        if app_images:
            user_app.app_images.set(app_images)

        return user_app


class UserAppBannerService:
    model = UserAppBanner

    @classmethod
    def filter(cls, **filters):
        return cls.model.objects.filter(**filters)

    @classmethod
    def get(cls, *args, **kwargs) -> UserAppBanner:
        try:
            return cls.model.objects.get(*args, **kwargs)
        except cls.model.DoesNotExist:
            raise ObjectNotFoundException(_('UserAppBanner not found'))

    @classmethod
    def create_banners(cls, image_ids: list[File]) -> list[UserAppBanner]:
        banners = [
            UserAppBanner.objects.create(image=image)
            for image in image_ids
        ]
        return banners
