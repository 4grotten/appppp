from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from shop.tests.factories import ShopItemFactory, ItemCategoryFactory, ItemSubcategoryFactory
from users.tests.factories import UserFactory


class ItemCategoryRetrieveViewTestCase(APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def setUp(self) -> None:
        self.category_one = ItemCategoryFactory(name='Cat 1')

        self.subcategory_one = ItemSubcategoryFactory(category=self.category_one, organization=None)
        self.subcategory_two = ItemSubcategoryFactory(category=self.category_one, organization=None)

        self.shop_item_with_price = ShopItemFactory(price=1200, subcategory=self.subcategory_one)
        self.shop_item_without_price = ShopItemFactory(price=None, subcategory=self.subcategory_two)

        self.url = reverse("v1:item_category_details", kwargs={"pk": self.category_one.id})

    def test_only_subcategories_with_items_with_prices_are_listed(self):
        response = self.client.get(self.url, content_type='application/json')

        expected_data = {
            "id": self.category_one.id,
            "icon": self.category_one.icon,
            "name": self.category_one.name,
            "subcategories": [
                {
                    "id": self.subcategory_one.id,
                    "name": self.subcategory_one.name,
                    "organization": None,
                    "icon": self.category_one.icon
                }
            ]
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)


class NonEmptyCategoryListViewTestCase(APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def setUp(self) -> None:
        self.category_one = ItemCategoryFactory(name='Cat 1', icon=None)
        self.category_two = ItemCategoryFactory(name='Cat 2', icon=None)
        self.subcategory_one = ItemSubcategoryFactory(category=self.category_one, organization=None)
        self.subcategory_two = ItemSubcategoryFactory(category=self.category_two, organization=None)

        self.shop_item_with_price = ShopItemFactory(price=1200, subcategory=self.subcategory_one)
        self.shop_item_without_price = ShopItemFactory(price=None, subcategory=self.subcategory_two)

        self.url = reverse("v1:non_empty_categories")

    def test_only_categories_with_items_with_prices_are_returned(self):
        response = self.client.get(self.url, content_type='application/json')

        expected_data = [
            {
                "id": self.category_one.id,
                "name": self.category_one.name,
                "icon": self.category_one.icon
            }
        ]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
