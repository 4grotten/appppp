import json
import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import OrganizationFactory
from shop.tests.factories import (
    ShopItemFactory, ItemBookmarkFactory
)
from users.tests.factories import (
    UserFactory,
)


class BookmarkListCreateViewTestCase(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.user = UserFactory()
        self.url = reverse("v1:bookmark_list_create")

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.get(
            self.url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_required_fields(self):
        self.client.force_authenticate(user=self.user)
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "is_bookmarked": ["This field is required."],
                "item": ['This field is required.']
            }
        }

        response = self.client.post(
            self.url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_bookmark_list(self):
        self.client.force_authenticate(user=self.user)
        organization = OrganizationFactory(owner=self.user)
        shop_item = ShopItemFactory(organization=organization)
        ItemBookmarkFactory(
            user=self.user,
            item=shop_item,
        )
        expected_data = {
            "total_count": 1,
            "total_pages": 1,
            "list": [
                {
                    "id": shop_item.id,
                    "name": shop_item.name,
                    "description": shop_item.description,
                    "article": shop_item.article,
                    "price": shop_item.price,
                    "discount": shop_item.discount,
                    "instagram_link": shop_item.instagram_link,
                    "is_published": shop_item.is_published,
                    "is_hidden": False,
                    "is_liked": False,
                    "is_bookmarked": True,
                    "like_count": 0,
                    "created_at": shop_item.created_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "updated_at": shop_item.updated_at.strftime(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    "youtube_links": shop_item.youtube_links,
                    "subcategory": shop_item.subcategory,
                    "images": [],
                    "organization": {
                        "id": organization.id,
                        "title": organization.title,
                        "image": {
                            "id": organization.image.id,
                            "file": f"http://testserver{organization.image.file.url}",
                            "name": os.path.basename(
                                organization.image.file.name),
                            "large": f"http://testserver{organization.image.large.url}",
                            "medium": f"http://testserver{organization.image.medium.url}",
                            "small": f"http://testserver{organization.image.small.url}",
                        },
                        "currency": "USD",
                        "types": [],
                        "phone_numbers": [],
                        "permissions": {
                            "is_owner": True,
                            "can_sale": True,
                            "can_check_attendance": True,
                            "can_see_stats": True,
                            "can_edit_organization": True,
                            "can_send_message": True,
                            "can_edit_partner": True
                        }
                    },
                    "instagram_data":
                        {
                            "videos": [],
                            "images": []
                        },
                    "is_updated": False
                }
            ]
        }

        response = self.client.get(
            self.url,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)

    def test_add_bookmark_to_shop_item(self):
        self.client.force_authenticate(user=self.user)
        organization = OrganizationFactory(owner=self.user)
        shop_item = ShopItemFactory(organization=organization)
        data = {
            "item": shop_item.id,
            "is_bookmarked": True
        }
        expected_data = {
            "message": "Successfully updated bookmark status"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)

    def test_remove_bookmark_from_shop_item(self):
        self.client.force_authenticate(user=self.user)
        organization = OrganizationFactory(owner=self.user)
        shop_item = ShopItemFactory(organization=organization)
        data = {
            "item": shop_item.id,
            "is_bookmarked": False
        }
        expected_data = {
            "message": "Successfully updated bookmark status"
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
