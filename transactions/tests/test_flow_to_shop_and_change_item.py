import json
import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from organizations.tests.factories import (
    OrganizationFactory
)
from shop.tests.factories import ShopItemFactory, CartFactory
from transactions.models import Transaction
from transactions.tests.factories import TransactionFactory
from users.tests.factories import UserFactory


class FlowToShopAndChangeItemTestCase(APITestCase):
    maxDiff = None

    def setUp(self):
        self.user = UserFactory(phone_number='+996550778133')
        self.client_user = UserFactory()
        self.organization = OrganizationFactory(
            title="TOYJOY",
            address="Улица хуево дом кукуева",
            owner=self.user
        )
        self.item = ShopItemFactory(
            name="Фалловибратор Baile. F9",
            organization=self.organization
        )
        self.transaction = TransactionFactory(
            client=self.client_user,
            processed_by=self.user,
            is_processed=False,
            status=Transaction.IN_PROGRESS,
            type=Transaction.ONLINE,
            organization=self.organization,
            delivery_type=Transaction.CASH_COURIER,
            employee_role="Owner",
            employee_avatar=None
        )
        self.cart = CartFactory(
            user=self.user,
            organization=self.organization,
            transaction=self.transaction
        )

    def test_flow_to_shop_and_change_item_with_order_delivery(self):
        self.client.force_authenticate(user=self.user)

        # Добавление товара в корзину
        add_cart_item_url = reverse("v1:add_cart_item")
        add_cart_item_data = {
            "item": self.item.id,
            "change": 1
        }
        add_cart_item_expected_data = {
            "item": self.item.id,
            "count": 1
        }
        add_cart_item_response = self.client.post(
            add_cart_item_url,
            data=json.dumps(add_cart_item_data),
            content_type='application/json'
        )

        self.assertEqual(add_cart_item_response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(
            add_cart_item_response.content, add_cart_item_expected_data)

        # Получаем список корзин по текущему пользователю
        user_carts_list_url = reverse("v1:user_cart_list")
        user_carts_list_response = self.client.get(
            user_carts_list_url,
            content_type='application/json'
        )
        user_carts_list_expected_data = {
            "total_count": 1,
            "total_pages": 1,
            "list": [
                {
                    "id": self.cart.id,
                    "items_count": 1,
                    "totals": {
                        "original_price": 0.0,
                        "discounted_price": 0.0
                    },
                    "organization": {
                        "id": self.organization.id,
                        "title": self.organization.title,
                        "currency": "USD",
                        "types": [],
                        "image": {
                            "id": self.organization.image.id,
                            "file": f"http://testserver{self.organization.image.file.url}",
                            "name": os.path.basename(
                                str(self.organization.image.file)),
                            "large": f"http://testserver{self.organization.image.large.url}",
                            "medium": f"http://testserver{self.organization.image.medium.url}",
                            "small": f"http://testserver{self.organization.image.small.url}",
                        },
                        "address": self.organization.address
                    },
                    "images": []
                }
            ]
        }

        self.assertEqual(
            user_carts_list_response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(
            user_carts_list_response.content, user_carts_list_expected_data)

        cart_id = user_carts_list_response.json().get("list")[0].get("id")
        # Оформляем заказ на адрес и номер
        order_delivery_url = reverse(
            "v1:order_delivery",
            kwargs={
                "pk": cart_id
            }
        )
        order_delivery_data = {
            "address": "Боконбаева",
            "phone": "+996500441420"
        }
        order_delivery_expected_data = {
            "message": "Success"
        }

        order_delivery_response = self.client.post(
            order_delivery_url,
            data=json.dumps(order_delivery_data),
            content_type='application/json'
        )

        self.assertEqual(
            order_delivery_response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(
            order_delivery_response.content, order_delivery_expected_data)

        #2 order_self_pickup_url = reverse("v1:order_self_pickup")

        user_cart_details_url = reverse(
            "v1:user_cart_details",
            kwargs={"pk": cart_id}
        )
        user_cart_details_data = {
            "items": [{
                "item": self.item.id,
                "count": 1
            }]
        }

        user_cart_details_expected_data = {
            "id": self.transaction.id,
            "currency": "USD",
            "original_amount": 0.0,
            "discount_percent": 0,
            "savings": 0.0,
            "from_cashback": 0.0,
            "to_cashback": 0.0,
            "final_amount": 0.0,
            "processed_by": self.transaction.processed_by.id,
            "employee_name": self.cart.transaction.employee_name,
            "employee_avatar": {
                "id": self.user.avatar.id,
                "file": f"http://testserver{self.user.avatar.file.url}",
                "name": os.path.basename(
                            str(self.user.avatar.file)
                ),
                "large": f"http://testserver{self.user.avatar.large.url}",
                "medium": f"http://testserver{self.user.avatar.medium.url}",
                "small": f"http://testserver{self.user.avatar.small.url}",
            },
            "employee_role": self.cart.transaction.employee_role,
            "updated_at": self.cart.transaction.updated_at.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "created_at": self.cart.transaction.created_at.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "client": {
                "id": self.cart.transaction.client.id,
                "full_name": self.cart.transaction.client.full_name,
                "avatar": {
                    "id": self.cart.transaction.client.avatar.id,
                    "file": f"http://testserver{self.cart.transaction.client.avatar.file.url}",
                    "name": os.path.basename(
                                str(self.cart.transaction.client.avatar.file)
                    ),
                    "large": f"http://testserver{self.cart.transaction.client.avatar.large.url}",
                    "medium": f"http://testserver{self.cart.transaction.client.avatar.medium.url}",
                    "small": f"http://testserver{self.cart.transaction.client.avatar.small.url}",
                },
            },
            "delivery_type": Transaction.CASH_COURIER,
            "type": Transaction.ONLINE,
            "cart": {
                "id": self.cart.id,
                "organization": {
                    "id": self.organization.id,
                    "title": self.organization.title,
                    "currency": "USD",
                    "types": [],
                    "image": {
                        "id": self.organization.image.id,
                        "file": f"http://testserver{self.organization.image.file.url}",
                        "name": os.path.basename(
                            str(self.organization.image.file)),
                        "large": f"http://testserver{self.organization.image.large.url}",
                        "medium": f"http://testserver{self.organization.image.medium.url}",
                        "small": f"http://testserver{self.organization.image.small.url}",
                    },
                    "address": self.organization.address
                },
                "totals": {
                    "original_price": 0.0,
                    "discounted_price": 0.0
                },
                "items": [
                    {
                        "item": {
                            "id": self.item.id,
                            "name": self.item.name,
                            "price": None,
                            "discounted_price": None,
                            "image": {
                                "file": None,
                                "is_watermarked": False
                            }
                        },
                        "count": 1
                    }
                ]
            },
            "status": Transaction.ACCEPTED,
            "current_user_can_see_stats": True,
            "delivery_info": None,
            "fixed_cart": None
        }

        user_cart_details_response = self.client.put(
            user_cart_details_url,
            data=json.dumps(user_cart_details_data),
            content_type='application/json'
        )

        self.assertEqual(
            user_cart_details_response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(
            user_cart_details_response.content, user_cart_details_expected_data)

        transaction_id = user_cart_details_response.json().get("id")
        from_cashback = user_cart_details_response.json().get("from_cashback")
        online_transaction_complete_url = reverse("v1:online_transaction_complete")
        online_transaction_complete_data = {
            "transaction_id": transaction_id,
            "from_cashback": from_cashback
        }
        online_transaction_complete_expected_data = {

        }

        online_transaction_complete_response = self.client.post(
            online_transaction_complete_url,
            data=json.dumps(online_transaction_complete_data),
            content_type='application/json'
        )

        print("online_transaction_complete_response=", online_transaction_complete_response.content)
        self.assertEqual(
            online_transaction_complete_response.status_code,
            status.HTTP_200_OK
        )
        self.assertJSONEqual(
            online_transaction_complete_response.content,
            online_transaction_complete_expected_data
        )
