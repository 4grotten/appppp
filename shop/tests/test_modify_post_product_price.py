import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from shop.tests.factories import ShopItemFactory

from organizations.tests.factories import OrganizationFactory
from users.tests.factories import (
    UserFactory,
    TokenFactory,
)


class ModifyPostProductPriceTestCase(APITestCase):
    def setUp(self) -> None:
        self.user = UserFactory(phone_number="996550771231")
        self.token = TokenFactory(user=self.user)
        self.organization = OrganizationFactory(
            title="Хуй пизда джигурда",
            owner=self.user
        )
        self.product = ShopItemFactory(
            organization=self.organization,
            price=12.5,
            discount=10,
            article="123ART",
        )

        self.post = ShopItemFactory(
            organization=self.organization,
            article="123ART",
        )

        self.client.force_authenticate(user=self.user)

    def test_modify_product_to_post_acceptable_item_price_none(self):
        self.client.force_authenticate(user=self.user)
        do_change_item_count_response = self.client.post(
            reverse("v1:add_cart_item"),
            data=json.dumps({"item": self.product.id, "change": 1}),
            content_type='application/json'
        )
        self.assertEqual(
            do_change_item_count_response.status_code,
            status.HTTP_200_OK
        )

        product_data = {
            "organization": self.organization.id,
            "name": "Да похуй ебани что-нибудь",
            "price": None
        }

        item_details_response = self.client.put(
            reverse("v1:item_details", kwargs={"pk": self.product.id}),
            data=json.dumps(product_data),
            content_type='application/json'
        )

        self.assertEqual(
            item_details_response.status_code,
            status.HTTP_200_OK
        )

    def test_modify_product_to_product_acceptable(self):
        post_data = {
            "organization": self.organization.id,
            "name": "Да похуй ебани что-нибудь",
        }

        item_details_response = self.client.put(
            reverse("v1:item_details", kwargs={"pk": self.product.id}),
            data=json.dumps(post_data),
            content_type='application/json'
        )

        self.assertEqual(
            item_details_response.status_code,
            status.HTTP_200_OK
        )
