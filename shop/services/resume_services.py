from django.utils.translation import gettext_lazy as _

from common.exceptions import ObjectNotFoundException
from common.models import Languages
from common.serializers import LanguagesListSerializer
from shop.models import ResumeInfo, ShopItem


class ResumeInfoService:
    @classmethod
    def get(cls, **filters):
        try:
            return ResumeInfo.objects.get(**filters)
        except ResumeInfo.DoesNotExist:
            raise ObjectNotFoundException(_('ShopItem not found'))

    @classmethod
    def create_resume(cls, item: ShopItem, gender=None, full_name=None, date_of_birth=None, languages=None, files=None):
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
            for index, file in enumerate(files):
                file.order = index
                file.save(update_fields=('order',))
                resume_info.files.add(file)
            resume_info.save()

        return resume_info
