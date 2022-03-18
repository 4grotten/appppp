from decimal import Decimal
import os
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import OrganizationFactory
from shop.tests.factories import (
    ShopItemFactory,
)
from users.tests.factories import (
    UserFactory,
)


class OrganizationItemListViewTestCase(APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def setUp(self) -> None:
        self.organization = OrganizationFactory(owner=self.user)
        self.shop_item_one = ShopItemFactory(
            organization=self.organization,
            name="Вибропуля Rabbit",
            price=Decimal("1179.00"),
        )
        self.shop_item_two = ShopItemFactory(
            organization=self.organization,
            name="Amur 2",
            price=Decimal("799.00"),
        )
        self.url = reverse("v1:organization_items-list")

    def test_required_fields(self):
        expected_data = {
            "message": "Valid organization is required in query parameters"
        }

        response = self.client.get(
            self.url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_organization_item_list(self):
        data = {
            "organization": self.organization.id
        }
        expected_data = {
            "total_count": 2,
            "total_pages": 1,
            "list": [
                {
                    "id": self.shop_item_two.id,
                    "name": self.shop_item_two.name,
                    'name_lang': self.shop_item_two.name_lang,
                    "description": self.shop_item_two.description,
                    'description_lang': self.shop_item_two.description_lang,
                    "article": self.shop_item_two.article,
                    "price": self.shop_item_two.price,
                    "discount": 0,
                    "instagram_link": None,
                    "is_published": self.shop_item_two.is_published,
                    "is_liked": False,
                    "is_bookmarked": False,
                    'is_hidden': self.shop_item_two.is_hidden,
                    "like_count": 0,
                    "created_at": self.shop_item_two.created_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%f"
                    )+"+00:00",
                    "updated_at": self.shop_item_two.updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "youtube_links": None,
                    "subcategory": None,
                    "images": [],
                    "organization": {
                        "id": self.organization.id,
                        "title": self.organization.title,
                        "image": {
                            "id": self.organization.image.id,
                            "file": f"{self.organization.image.file.url}",
                            "name": os.path.basename(
                                self.organization.image.file.name),
                            "large": f"{self.organization.image.large.url}",
                            "medium": f"{self.organization.image.medium.url}",
                            "small": f"{self.organization.image.small.url}",
                        },
                        "currency": "USD",
                        "types": [],
                        "phone_numbers": [],
                        'promo_cashback': None,
                        "permissions": None,
                        'verification_status': self.organization.verification_status,
                    },
                    "instagram_data": {
                        "videos": [],
                        "images": []
                    },
                    "is_updated": False
                },
                {
                    "id": self.shop_item_one.id,
                    "name": self.shop_item_one.name,
                    'name_lang': self.shop_item_one.name_lang,
                    "description": self.shop_item_one.description,
                    'description_lang': self.shop_item_one.description_lang,
                    "article": self.shop_item_one.article,
                    "price": self.shop_item_one.price,
                    "discount": 0,
                    "instagram_link": None,
                    "is_published": self.shop_item_one.is_published,
                    "is_liked": False,
                    "is_bookmarked": False,
                    "is_hidden": self.shop_item_one.is_hidden,
                    "like_count": 0,
                    "created_at": self.shop_item_one.created_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%f"
                    )+"+00:00",
                    "updated_at": self.shop_item_one.updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "youtube_links": None,
                    "subcategory": None,
                    "images": [],
                    "organization": {
                        "id": self.organization.id,
                        "title": self.organization.title,
                        "image": {
                            "id": self.organization.image.id,
                            "file": f"{self.organization.image.file.url}",
                            "name": os.path.basename(
                                self.organization.image.file.name),
                            "large": f"{self.organization.image.large.url}",
                            "medium": f"{self.organization.image.medium.url}",
                            "small": f"{self.organization.image.small.url}",
                        },
                        "currency": "USD",
                        "types": [],
                        "phone_numbers": [],
                        'promo_cashback': None,
                        "permissions": None,
                        'verification_status': self.organization.verification_status,
                    },
                    "instagram_data": {
                        "videos": [],
                        "images": []
                    },
                    "is_updated": False
                }
            ],
            "has_new": False
        }

        response = self.client.get(
            self.url,
            data=data,
            content_type='application/json'
        )
        print(response.content)
        print('----------------------------------')
        print(expected_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
