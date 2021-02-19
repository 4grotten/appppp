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
        self.shop_item = ShopItemFactory(
            organization=self.organization,
            price=12.5,
            discount=10,
            article="123ART",
        )

    def test_user_not_register(self):
        self.client.force_authenticate(user=self.user)
        do_change_item_count_response = self.client.post(
            reverse("v1:add_cart_item"),
            data=json.dumps({"item": self.shop_item.id, "change": 1}),
            content_type='application/json'
        )
        self.assertEqual(
            do_change_item_count_response.status_code,
            status.HTTP_200_OK
        )

        item_data = {
            "organization": self.organization.id,
            "name": "Да похуй ебани что-нибудь",
            "price": 0,
            "discount": 0
        }
        item_details_response = self.client.put(
            reverse("v1:item_details", kwargs={"pk": self.shop_item.id}),
            data=json.dumps(item_data),
            content_type='application/json'
        )
        self.assertEqual(
            item_details_response.status_code,
            status.HTTP_200_OK
        )

        carts_response = self.client.get(
            reverse("v1:user_cart_list"),
            content_type='application/json'
        )
        cart_id = carts_response.json().get("list")[0].get("id")
        cart_response = self.client.get(
            reverse("v1:user_cart_details", kwargs={"pk": cart_id}),
            content_type='application/json'
        )
        self.assertEqual(
            cart_response.json().get("items")[0].get("item").get("id"),
            self.shop_item.id
        )
