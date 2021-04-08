from decimal import Decimal

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
        self.url = reverse("v1:organization_items")

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
                    "description": self.shop_item_two.description,
                    "article": self.shop_item_two.article,
                    "price": self.shop_item_two.price,
                    "discount": 0,
                    "instagram_link": None,
                    "is_published": self.shop_item_two.is_published,
                    "is_liked": False,
                    "is_bookmarked": False,
                    "like_count": 0,
                    "created_at": self.shop_item_two.created_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "updated_at": self.shop_item_two.updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "youtube_links": None,
                    "subcategory": None,
                    "images": [],
                    "instagram_data": {
                        "videos": [],
                        "images": []
                    },
                    "is_updated": False
                },
                {
                    "id": self.shop_item_one.id,
                    "name": self.shop_item_one.name,
                    "description": self.shop_item_one.description,
                    "article": self.shop_item_one.article,
                    "price": self.shop_item_one.price,
                    "discount": 0,
                    "instagram_link": None,
                    "is_published": self.shop_item_one.is_published,
                    "is_liked": False,
                    "is_bookmarked": False,
                    "like_count": 0,
                    "created_at": self.shop_item_one.created_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "updated_at": self.shop_item_one.updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "youtube_links": None,
                    "subcategory": None,
                    "images": [],
                    "instagram_data": {
                        "videos": [],
                        "images": []
                    },
                    "is_updated": False
                }
            ]
        }

        response = self.client.get(
            self.url,
            data=data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
