import json
import re

from django.urls import reverse
from rest_framework.test import APITestCase
from unittest import expectedFailure

from common.tests.factories import CurrencyFactory
from organizations.models import OrganizationClientFinancialStatus, DiscountCard
from organizations.tests.factories import (
    OrganizationFactory, OrganizationClientFinancialStatusFactory, DiscountCardFactory, RoleFactory, MembershipFactory
)
from organizations.tests.test_utils import PartnershipUtils
from shop.models import Cart
from shop.tests.factories import CartFactory, ShopItemFactory, CartItemFactory
from transactions.models import Transaction
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory, TokenFactory


class UpdateCartTestCase(APITestCase):
    def setUp(self):
        self.url = 'v1:user_cart_details'
        self.user_owner = UserFactory(phone_number='123456789', full_name='Owner')
        self.token_owner = TokenFactory(user=self.user_owner)
        self.header_owner = {"HTTP_AUTHORIZATION": f"Token {self.token_owner}"}

        self.currency = CurrencyFactory(code='XXX')
        self.organization = OrganizationFactory(owner=self.user_owner, currency=self.currency, cashback_group=None)

        self.role_admin = RoleFactory(
            title='admin', organization=self.organization, can_sale=True,
            can_check_attendance=True, can_see_stats=True, can_edit_organization=True,
            can_send_message=True, can_edit_partner=True)
        self.user_admin = UserFactory(phone_number='+996777009900')
        self.membership = MembershipFactory(organization=self.organization, user=self.user_admin, role=self.role_admin)

        self.client_user = UserFactory(phone_number='777777777')
        self.client_user2 = UserFactory(phone_number='777777755')

    def test_client_update_open_cart_successfully(self):
        shop_item1 = ShopItemFactory(organization=self.organization, price=100, discount=10)
        shop_item2 = ShopItemFactory(organization=self.organization, price=200, discount=10)
        cart = CartFactory(user=self.client_user, organization=self.organization)
        cart_item1 = CartItemFactory(cart=cart, item=shop_item1, count=5)
        cart_item2 = CartItemFactory(cart=cart, item=shop_item2, count=10)
        token_client = TokenFactory(user=self.client_user)
        data = {
            "items": [
                {
                    "item": shop_item1.id,
                    "count": 10
                },
            ]
        }
        header = {"HTTP_AUTHORIZATION": f"Token {token_client}"}
        response = self.client.put(reverse(self.url, kwargs={"pk": cart.id}), **header,
                                   content_type='application/json', data=json.dumps(data))
        cart1 = Cart.objects.get(id=cart.id)
        self.assertEqual(response.status_code, 200)

    def test_update_cart_fail_on_transaction_status(self):
        shop_item1 = ShopItemFactory(organization=self.organization, price=100, discount=10)
        shop_item2 = ShopItemFactory(organization=self.organization, price=200, discount=10)
        transaction = TransactionFactory(status='accepted')
        cart = CartFactory(user=self.client_user, organization=self.organization, is_open=False,
                           transaction=transaction)
        cart_item1 = CartItemFactory(cart=cart, item=shop_item1, count=5)
        cart_item2 = CartItemFactory(cart=cart, item=shop_item2, count=10)

        data = {
            "items": [
                {
                    "item": shop_item1.id,
                    "count": 10
                },
            ]
        }
        header = {"HTTP_AUTHORIZATION": f"Token {self.token_owner}"}
        response = self.client.put(reverse(self.url, kwargs={"pk": cart.id}), **header,
                                   content_type='application/json', data=json.dumps(data))
        self.assertEqual(response.status_code, 403)

    def test_update_cart_client_fail_on_closed_cart(self):
        shop_item1 = ShopItemFactory(organization=self.organization, price=100, discount=10)
        shop_item2 = ShopItemFactory(organization=self.organization, price=200, discount=10)
        cart = CartFactory(user=self.client_user, organization=self.organization, is_open=False)
        cart_item1 = CartItemFactory(cart=cart, item=shop_item1, count=5)
        cart_item2 = CartItemFactory(cart=cart, item=shop_item2, count=10)
        token_client = TokenFactory(user=self.client_user)
        data = {
            "items": [
                {
                    "item": shop_item1.id,
                    "count": 10
                },
            ]
        }
        header = {"HTTP_AUTHORIZATION": f"Token {token_client}"}
        response = self.client.put(reverse(self.url, kwargs={"pk": cart.id}), **header,
                                   content_type='application/json', data=json.dumps(data))
        cart1 = Cart.objects.get(id=cart.id)
        self.assertEqual(response.status_code, 403)

    def test_organization_update_cart_accepted_on_closed_cart(self):
        shop_item1 = ShopItemFactory(organization=self.organization, price=100, discount=10)
        shop_item2 = ShopItemFactory(organization=self.organization, price=200, discount=10)
        transaction = TransactionFactory(status='in_progress')
        cart = CartFactory(user=self.client_user, organization=self.organization, is_open=True, transaction=transaction)
        cart_item1 = CartItemFactory(cart=cart, item=shop_item1, count=5)
        cart_item2 = CartItemFactory(cart=cart, item=shop_item2, count=10)
        token_client = TokenFactory(user=self.client_user)
        data = {
            "items": [
                {
                    "item": shop_item1.id,
                    "count": 10
                },
            ]
        }
        header = {"HTTP_AUTHORIZATION": f"Token {self.token_owner}"}
        response = self.client.put(reverse(self.url, kwargs={"pk": cart.id}), **header,
                                   content_type='application/json', data=json.dumps(data))
        cart1 = Cart.objects.get(id=cart.id)
        self.assertEqual(response.status_code, 200)

    def test_user_update_cart_fail_on_serializer(self):
        shop_item1 = ShopItemFactory(organization=self.organization, price=100, discount=10)
        shop_item2 = ShopItemFactory(organization=self.organization, price=200, discount=10)
        transaction = TransactionFactory(status='in_progress')
        cart = CartFactory(user=self.client_user, organization=self.organization, is_open=True, transaction=transaction)
        cart_item1 = CartItemFactory(cart=cart, item=shop_item1, count=5)
        cart_item2 = CartItemFactory(cart=cart, item=shop_item2, count=10)
        token_client = TokenFactory(user=self.client_user)
        data = {
            "items": [
                {
                    "item": -1,
                    "count": 10
                },
            ]
        }
        header = {"HTTP_AUTHORIZATION": f"Token {self.token_owner}"}
        response = self.client.put(reverse(self.url, kwargs={"pk": cart.id}), **header,
                                   content_type='application/json', data=json.dumps(data))
        cart1 = Cart.objects.get(id=cart.id)
        self.assertEqual(response.status_code, 406)
