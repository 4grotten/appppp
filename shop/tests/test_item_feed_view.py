from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import OrganizationFactory
from shop.tests.factories import ShopItemFactory
from users.tests.factories import UserFactory


class FeedViewTestCase(APITestCase):
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()

    def setUp(self) -> None:
        self.organization = OrganizationFactory(owner=self.user, image=None)
        self.shop_item_one = ShopItemFactory(organization=self.organization, price=1179)
        self.shop_item_two = ShopItemFactory(organization=self.organization, price=799)

        self.banned_organization = OrganizationFactory(owner=self.user, image=None, is_banned=True)
        self.banned_org_item = ShopItemFactory(organization=self.banned_organization, price=300)

        self.url = reverse("v1:shop_feed")

    def test_banned_organization_items_are_not_returned(self):
        response = self.client.get(self.url, content_type='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['total_count'], 2)
