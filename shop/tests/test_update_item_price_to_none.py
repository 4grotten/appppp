import json
import os
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from common.tests.factories import CurrencyFactory
from organizations.tests.factories import (
    OrganizationFactory, RoleFactory, MembershipFactory
)
from shop.tests.factories import CartFactory, ShopItemFactory, CartItemFactory
from users.tests.factories import UserFactory, TokenFactory


class UpdateItemPriceToNoNeTestCase(APITestCase):
    maxDiff = None

    def setUp(self):
        self.url = 'v1:user_cart_details'
        self.user_owner = UserFactory(phone_number='123456789', full_name='Owner')
        self.token_owner = TokenFactory(user=self.user_owner)
        self.header_owner = {"HTTP_AUTHORIZATION": f"Token {self.token_owner}"}

        self.currency = CurrencyFactory(code='XXX')
        self.organization = OrganizationFactory(owner=self.user_owner, currency=self.currency, cashback_group=None)

        self.client_user = UserFactory(phone_number='777777777')
        self.client_user2 = UserFactory(phone_number='777777755')

    def test_item_price_O_delete_cart_item_and_cart_successfully(self):
        shop_item1 = ShopItemFactory(organization=self.organization, price=Decimal(100), discount=10)
        shop_item2 = ShopItemFactory(organization=self.organization, price=Decimal(200), discount=10)
        cart = CartFactory(user=self.user_owner, organization=self.organization, is_open=True)
        CartItemFactory(cart=cart, item=shop_item2, count=10)
        CartItemFactory(cart=cart, item=shop_item1, count=5)
        self.client.force_authenticate(user=self.user_owner)
        product_data = {
            "organization": self.organization.id,
            "name": "Да похуй ебани что-нибудь",
            "price": None
        }

        item_details_response = self.client.put(
            reverse("v1:item_details", kwargs={"pk": shop_item1.id}),
            data=json.dumps(product_data),
            content_type='application/json'
        )

        self.assertEqual(
            item_details_response.status_code,
            status.HTTP_200_OK
        )

        expected_data_cart_detail = {
            "id": cart.id,
            "can_sell": True,
            "organization":
                {
                    "id": self.organization.id,
                    "title": self.organization.title,
                    "currency": self.organization.currency.code,
                    "types": [],
                    "image":
                        {
                            "id": self.organization.image.id,
                            "file": f"{self.organization.image.file.url}",
                            "name": os.path.basename(
                                str(self.organization.image.file)),
                            "large": f"{self.organization.image.large.url}",
                            "medium": f"{self.organization.image.medium.url}",
                            "small": f"{self.organization.image.small.url}",
                        },
                    "address": None,
                    "has_delivery": self.organization.has_delivery,
                    "has_self_pick_up": self.organization.has_self_pick_up,
                    "opens_at": self.organization.opens_at,
                    "closes_at": self.organization.closes_at,
                    "time_working": "closed",
                    "verification_status": self.organization.verification_status,
                    "avg_check": self.organization.avg_check,
                },
            "totals":
                {
                    "original_price": 2000.0,
                    "discounted_price": 1800.0
                },
            "items":
                [
                    {
                        "item":
                            {
                                "id": shop_item2.id,
                                "name": shop_item2.name,
                                "price": shop_item2.price,
                                "discounted_price": shop_item2.discounted_price,
                                "image": None
                            },
                        "count": 10
                    }
                ]
        }

        cart_details_response = self.client.get(reverse('v1:user_cart_details', kwargs={"pk": cart.id}),
                                                content_type='application/json')
        self.assertEqual(cart_details_response.status_code, 200)
        self.assertEqual(cart_details_response.json(), expected_data_cart_detail)

        item_details_response = self.client.put(
            reverse("v1:item_details", kwargs={"pk": shop_item2.id}),
            data=json.dumps(product_data),
            content_type='application/json'
        )

        self.assertEqual(
            item_details_response.status_code,
            status.HTTP_200_OK
        )

        cart_details_response = self.client.get(reverse('v1:user_cart_details', kwargs={"pk": cart.id}),
                                                content_type='application/json')
        self.assertEqual(cart_details_response.status_code, status.HTTP_404_NOT_FOUND)
