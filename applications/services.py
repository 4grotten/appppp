from typing import Optional, List

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import QuerySet, Q, Case, When, Value, IntegerField

from applications.models import UserApp, UserAppBanner, UserAppType, UserAppPurchase
from common.exceptions import ObjectNotFoundException, IntegrityException, NotAcceptableException
from django.utils.translation import gettext_lazy as _

from common.models import File
from transactions.services.transaction_services import TransactionService
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
                           company_name: Optional[str] = None,
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
            company_name=company_name,
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

    @classmethod
    @transaction.atomic
    def update(cls, application, image_id, validated_data):
        try:
            from common.models import File

            image = File.objects.get(id=image_id)
            application.image = image

            selected_banner_id = validated_data.pop('selected_banner_id', None)
            if selected_banner_id:
                from applications.models import UserAppBanner  # путь проверь
                selected_banner = UserAppBanner.objects.get(id=selected_banner_id)
                application.selected_banner = selected_banner
            else:
                application.selected_banner = None

            for attr, value in validated_data.items():
                if attr == 'types':
                    application.types.set(value)
                elif attr == 'app_images':
                    application.app_images.set(value)
                else:
                    setattr(application, attr, value)

            application.save()
            return application

        except ObjectDoesNotExist as e:
            raise IntegrityException(_('Not found: {e}').format(e=str(e)))
        except Exception as e:
            raise IntegrityException(_('Could not update application: {e}').format(e=str(e)))

    @classmethod
    def get_application_banners(cls, application: UserApp) -> QuerySet:
        return UserAppBanner.objects.filter(
            Q(is_default=True) | Q(user_apps=application)
        ).annotate(
            sort_order=Case(
                When(is_default=False, then=Value(0)),
                When(is_default=True, then=Value(1)),
                output_field=IntegerField()
            )
        ).order_by('sort_order', '-created_at')

    @classmethod
    @transaction.atomic
    def create_app_purchase(cls, user, app, processed_by, utc_offset_minutes=0):
        if not app.price:
            raise IntegrityException(_('This app is not for sale.'))

        transaction = TransactionService.create_user_app_transaction(
            user=user,
            processed_by=processed_by,
            application=app,
            utc_offset_minutes=utc_offset_minutes
        )

        # 2. Создание записи о покупке
        app_purchase = UserAppPurchase.objects.create(
            user=user,
            app=app,
            transaction=transaction,
            is_paid=False
        )

        return app_purchase

    @classmethod
    def update_visibility_status(cls, user: User, user_app: UserApp, is_hidden: bool):
        if user == user_app.owner:
            user_app.is_hidden = is_hidden
            user_app.save(update_fields=('is_hidden',))
        else:
            raise NotAcceptableException(_('No rights to edit this application'))


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
