import pandas as pd
from django.contrib.auth import get_user_model
import logging
from organizations.models import OrganizationType, Organization, PhoneNumber
from organizations.services.organization_services import OrganizationInstagramIntegrationService
import io
import requests

User = get_user_model()

ORGANIZATION_TITLE_LANG = 'RU'
ORGANIZATION_ADDRESS = "ORGANIZATION_ADDRESS"
ORGANIZATION_INSTAGRAM_LINK = "ORGANIZATION_INSTAGRAM_LINK"
ORGANIZATION_PHONE_2 = "ORGANIZATION_PHONE_2"
ORGANIZATION_PHONE_1 = "ORGANIZATION_PHONE_1"
ORGANIZATION_TYPE = "ORGANIZATION_TYPE"
ORGANIZTION_NAME = "ORGANIZTION_NAME"

COLUMNS_MAPPING = {
    ORGANIZTION_NAME: 0,
    ORGANIZATION_TYPE: 1,
    ORGANIZATION_PHONE_1: 2,
    ORGANIZATION_PHONE_2: 3,
    ORGANIZATION_INSTAGRAM_LINK: 4,
    ORGANIZATION_ADDRESS: 5,
}

ORGANIZATION_DEFAULT_COUNTRY_CODE = "KG"


def import_organization_for_user(user: User, file_path: str) -> int:
    if 'http' in file_path:
        s = requests.get(file_path).content
        df = pd.read_excel(io.BytesIO(s))
    else:
        df = pd.read_excel(file_path)
    count = 0
    for row in df.iterrows():
        organization_name = str(row[1][COLUMNS_MAPPING[ORGANIZTION_NAME]]).strip()
        organization_type_str = str(row[1][COLUMNS_MAPPING[ORGANIZATION_TYPE]]).strip()
        organization_phone_1 = str(row[1][COLUMNS_MAPPING[ORGANIZATION_PHONE_1]]).strip()
        organization_phone_2 = str(row[1][COLUMNS_MAPPING[ORGANIZATION_PHONE_2]]).strip()
        instagram_link = row[1][COLUMNS_MAPPING[ORGANIZATION_INSTAGRAM_LINK]].strip()
        address = row[1][COLUMNS_MAPPING[ORGANIZATION_ADDRESS]].strip()
        # country_code = ORGANIZATION_DEFAULT_COUNTRY_CODE
        organization_type = OrganizationType.objects.get(title_ru__iexact=organization_type_str)
        # print(organization_type, organization_name)
        # country = Country.objects.get(code=country_code)
        organization, created = Organization.objects.get_or_create(
            title=organization_name,
            title_lang=ORGANIZATION_TITLE_LANG,
            address=address,
            owner=user,
            # country=country
        )
        if organization_phone_1:
            phone1, created = PhoneNumber.objects.get_or_create(phone_number=organization_phone_1,
                                                                organization=organization)
        if organization_phone_2:
            phone2, created = PhoneNumber.objects.get_or_create(phone_number=organization_phone_2,
                                                                organization=organization)
        try:
            if instagram_link:
                OrganizationInstagramIntegrationService.create(organization, instagram_link)
        except Exception as e:
            logging.exception(e)
        if organization_type not in organization.types.all():
            organization.types.add(organization_type)
        count += 1

    return count
