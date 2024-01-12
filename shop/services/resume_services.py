from django.db import transaction
from django.db.models import QuerySet, Q
from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException
from common.models import Languages
from common.serializers import LanguagesListSerializer
from notifications.constants import NOTIFICATION_MODE_RESUME, REQUEST_RESUME_CLIENT_TYPE, REQUEST_RESUME_TYPE
from notifications.models import Notification
from notifications.tasks import sent_notification, send_notifications_organization_members
from organizations.models import Organization
from shop.models import ResumeInfo, ShopItem, ResumePhoneNumber, ResumeSocialNetwork, ResumeDetailInfo, \
    ResumeWorkExperience, ResumeEducation, ResumeRequest
from users.models import User
from users.services import PhoneNumberService, SocialNetworkContactService


class ResumeInfoService:
    @classmethod
    def get(cls, **filters):
        try:
            return ResumeInfo.objects.get(**filters)
        except ResumeInfo.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

    @classmethod
    def get_info_of_resume(cls, item: ShopItem):
        try:
            return ResumeInfo.objects.get(item=item)
        except ResumeInfo.DoesNotExist:
            return None

    @classmethod
    def update_resume_info(cls, item: ShopItem, gender=None, full_name=None, date_of_birth=None, languages=None, files=None):
        languages_list = []
        if languages:
            for language_code in languages:
                try:
                    language = Languages.objects.get(code=language_code)
                    serializer = LanguagesListSerializer(language)
                    languages_list.append(serializer.data)
                except Languages.DoesNotExist:
                    pass

        resume_info, created = ResumeInfo.objects.get_or_create(item=item)

        if not created:
            resume_info.gender = gender
            resume_info.full_name = full_name
            resume_info.date_of_birth = date_of_birth
            resume_info.languages = languages_list
            resume_info.files.clear()
            for index, file in enumerate(files):
                file.order = index
                file.save(update_fields=('order',))
                resume_info.files.add(file)
            resume_info.save()

        return resume_info


class ResumePhoneNumberService:
    model = ResumePhoneNumber

    @classmethod
    def get_numbers_of_resume(cls, item: ShopItem) -> QuerySet:
        return ResumePhoneNumber.objects.filter(item=item)

    @classmethod
    def update_resume_phone_numbers(cls, item: ShopItem, numbers: list):
        with transaction.atomic():
            ResumePhoneNumber.objects.filter(item=item).delete()
            numbers = [ResumePhoneNumber(item=item, phone_number=number) for number in numbers]
            ResumePhoneNumber.objects.bulk_create(numbers)
            return numbers


class ResumeSocialNetworkService:
    model = ResumeSocialNetwork

    @classmethod
    def get_networks_of_resume(cls, item: ShopItem) -> QuerySet:
        return ResumeSocialNetwork.objects.filter(item=item)

    @classmethod
    def update_resume_social_networks(cls, item: ShopItem, urls: list):
        with transaction.atomic():
            ResumeSocialNetwork.objects.filter(item=item).delete()
            contacts = [ResumeSocialNetwork(item=item, url=url) for url in urls]
            ResumeSocialNetwork.objects.bulk_create(contacts)
            return contacts


class ResumeDetailInfoService:
    model = ResumeDetailInfo

    @classmethod
    def get_detail_info_of_resume(cls, item: ShopItem):
        try:
            return ResumeDetailInfo.objects.get(item=item)
        except ResumeDetailInfo.DoesNotExist:
            return None

    @classmethod
    def update_resume_detail_info(cls, item: ShopItem, text: str):
        detail_info, created = ResumeDetailInfo.objects.get_or_create(item=item)
        detail_info.text = text
        detail_info.save()

        return detail_info


class ResumeWorkExperienceService:
    model = ResumeWorkExperience

    @classmethod
    def get_work_experiences_of_resume(cls, item: ShopItem) -> QuerySet:
        return ResumeWorkExperience.objects.filter(item=item)

    @classmethod
    def create_resume_work_experience(cls, item: ShopItem, work_experiences: list):
        with transaction.atomic():
            ResumeWorkExperience.objects.filter(item=item).delete()

            experiences = [
                ResumeWorkExperience(
                    item=item,
                    company_name=experience.get('company_name'),
                    position=experience.get('position'),
                    text=experience.get('text'),
                    start_of_work=experience.get('start_of_work'),
                    end_of_work=experience.get('end_of_work'),
                    up_to_now=experience.get('up_to_now', False)
                )
                for experience in work_experiences
            ]

            ResumeWorkExperience.objects.bulk_create(experiences)
            return experiences


class ResumeEducationService:
    model = ResumeEducation

    @classmethod
    def get_educations_of_resume(cls, item: ShopItem) -> QuerySet:
        return ResumeEducation.objects.filter(item=item)

    @classmethod
    def create_resume_education(cls, item: ShopItem, educations: list):
        with transaction.atomic():
            ResumeEducation.objects.filter(item=item).delete()

            final_educations = [
                ResumeEducation(
                    item=item,
                    school_name=education.get('school_name'),
                    category=education.get('category'),
                    text=education.get('text'),
                    start_of_study=education.get('start_of_study'),
                    end_of_study=education.get('end_of_study'),
                    up_to_now=education.get('up_to_now', False)
                )
                for education in educations
            ]

            ResumeEducation.objects.bulk_create(final_educations)
            return final_educations


class ResumeRequestService:

    @classmethod
    def get(cls, **filters):
        try:
            return ResumeRequest.objects.get(**filters)
        except ResumeRequest.DoesNotExist:
            raise ObjectNotFoundException(_('ResumeRequest not found'))


    @classmethod
    def process_user_resume_request(cls, sender_user: User, organization: Organization, item: ShopItem,
                                    user_contacts: bool, phone_numbers=None, links=None):
        if user_contacts:
            user_phone_numbers_list = []
            user_phone_numbers = PhoneNumberService.get_numbers_of_user(user_id=sender_user.id)
            for user_phone_number in user_phone_numbers:
                user_phone_numbers_list.append(user_phone_number.phone_number)

            user_links_list = []
            user_links = SocialNetworkContactService.get_networks_of_user(user_id=sender_user.id)
            for user_link in user_links:
                user_links_list.append(user_link.url)
            resume_request = ResumeRequest.objects.create(sender_user=sender_user, organization=organization,
                                                          item=item, phone_numbers=user_phone_numbers_list,
                                                          links=user_links_list)
        else:
            resume_request = ResumeRequest.objects.create(sender_user=sender_user, organization=organization,
                                                          item=item, user_contacts=user_contacts,
                                                          phone_numbers=phone_numbers, links=links)

        Notification.objects.filter(
            Q(extra_data__item_id=resume_request.item.id) &
            Q(extra_data__user_id=resume_request.sender_user.id) &
            (Q(type=REQUEST_RESUME_TYPE) | Q(type=REQUEST_RESUME_CLIENT_TYPE))).delete()

        sent_notification.delay(
            recipient_id=resume_request.sender_user.id,
            mode=NOTIFICATION_MODE_RESUME,
            notification_type=REQUEST_RESUME_CLIENT_TYPE,
            organization_id=resume_request.organization.id,
            extra_data=dict(item_id=resume_request.item.id,
                            resume_name=resume_request.item.name,
                            salary_from=str(resume_request.item.salary_from),
                            currency=resume_request.item.currency.code,
                            user_id=resume_request.sender_user.id)
        )
        send_notifications_organization_members.delay(
            members_organization_id=resume_request.organization.id,
            mode=NOTIFICATION_MODE_RESUME,
            sender_id=resume_request.sender_user.id,
            with_permissions=dict(can_see_stats=True),
            notification_type=REQUEST_RESUME_TYPE,
            organization_id=resume_request.organization.id,
            extra_data=dict(item_id=resume_request.item.id,
                            resume_name=resume_request.item.name,
                            salary_from=str(resume_request.item.salary_from),
                            currency=resume_request.item.currency.code,
                            user_id=resume_request.sender_user.id)
        )


