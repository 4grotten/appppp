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
        self.cart = CartFactory(
            user=self.user,
            organization=self.organization,
            transaction=None
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

        order_delivery_response = self.client.post(
            order_delivery_url,
            data=json.dumps(order_delivery_data),
            content_type='application/json'
        )

        transaction_id = order_delivery_response.json().get("transaction_id")
        self.assertEqual(
            order_delivery_response.status_code, status.HTTP_200_OK)
        self.assertTrue(transaction_id)

        # 2 order_self_pickup_url = reverse("v1:order_self_pickup")

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

        user_cart_details_response = self.client.put(
            user_cart_details_url,
            data=json.dumps(user_cart_details_data),
            content_type='application/json'
        )

        self.assertEqual(
            user_cart_details_response.status_code, status.HTTP_200_OK)

        _transaction_id = user_cart_details_response.json().get("id")
        from_cashback = user_cart_details_response.json().get("from_cashback")

        # Завершаем транзакцию.
        online_transaction_complete_url = reverse("v1:online_transaction_complete")
        online_transaction_complete_data = {
            "transaction_id": _transaction_id,
            "from_cashback": from_cashback
        }
        online_transaction_complete_expected_data = {
            "message": "Transaction successfully completed"
        }

        online_transaction_complete_response = self.client.post(
            online_transaction_complete_url,
            data=json.dumps(online_transaction_complete_data),
            content_type='application/json'
        )

        self.assertEqual(
            online_transaction_complete_response.status_code,
            status.HTTP_200_OK
        )
        self.assertJSONEqual(
            online_transaction_complete_response.content,
            online_transaction_complete_expected_data
        )
        self.assertEqual(transaction_id, _transaction_id)

    def test_flow_to_shop_and_change_item_with_order_delivery_change_item_after_completed(self):
        self.client.force_authenticate(user=self.user)

        item = ShopItemFactory(
            name="Фалловибратор Baile. F9 faf",
            organization=self.organization,
            price=100.0,
            discount=10.0
        )
        # Добавление товара в корзину
        add_cart_item_url = reverse("v1:add_cart_item")
        add_cart_item_data = {
            "item": item.id,
            "change": 1
        }
        add_cart_item_expected_data = {
            "item": item.id,
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
                        "original_price": 100.0,
                        "discounted_price": 90.0
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

        order_delivery_response = self.client.post(
            order_delivery_url,
            data=json.dumps(order_delivery_data),
            content_type='application/json'
        )

        transaction_id = order_delivery_response.json().get("transaction_id")
        self.assertEqual(
            order_delivery_response.status_code, status.HTTP_200_OK)
        self.assertTrue(transaction_id)

        # 2 order_self_pickup_url = reverse("v1:order_self_pickup")

        user_cart_details_url = reverse(
            "v1:user_cart_details",
            kwargs={"pk": cart_id}
        )
        user_cart_details_data = {
            "items": [{
                "item": item.id,
                "count": 1
            }]
        }

        transaction = Transaction.objects.get(id=transaction_id)
        user_cart_details_expected_data = {
            "id": transaction.id,
            "currency": "USD",
            "original_amount": 100.0,
            "discount_percent": 0,
            "savings": 10.0,
            "from_cashback": 0.0,
            "to_cashback": 0.0,
            "final_amount": 90.0,
            "processed_by": self.user.id,
            "employee_name": self.user.full_name,
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
            "employee_role": "Owner",
            "updated_at": transaction.updated_at.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "created_at": transaction.created_at.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "client": {
                "id": transaction.client.id,
                "full_name": transaction.client.full_name,
                "avatar": {
                    "id": transaction.client.avatar.id,
                    "file": f"http://testserver{transaction.client.avatar.file.url}",
                    "name": os.path.basename(
                        str(transaction.client.avatar.file)
                    ),
                    "large": f"http://testserver{transaction.client.avatar.large.url}",
                    "medium": f"http://testserver{transaction.client.avatar.medium.url}",
                    "small": f"http://testserver{transaction.client.avatar.small.url}",
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
                    "original_price": 100.0,
                    "discounted_price": 90.0
                },
                "items": [
                    {
                        "item": {
                            "id": item.id,
                            "name": item.name,
                            "price": 100.0,
                            "discounted_price": 90.0,
                            "image": {
                                "file": None,
                                "is_watermarked": False
                            }
                        },
                        "count": 1
                    }
                ]
            },
            "status": Transaction.IN_PROGRESS,
            "current_user_can_see_stats": True,
            "delivery_info": {
                "address": "Боконбаева",
                "apartment": None, "intercom": None, "entrance": None, "floor": None, "phone": "+996500441420",
                "comment": None},
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

        # Завершаем транзакцию.
        online_transaction_complete_url = reverse("v1:online_transaction_complete")
        online_transaction_complete_data = {
            "transaction_id": transaction_id,
            "from_cashback": from_cashback
        }
        online_transaction_complete_expected_data = {
            "message": "Transaction successfully completed"
        }

        online_transaction_complete_response = self.client.post(
            online_transaction_complete_url,
            data=json.dumps(online_transaction_complete_data),
            content_type='application/json'
        )

        self.assertEqual(
            online_transaction_complete_response.status_code,
            status.HTTP_200_OK
        )
        self.assertJSONEqual(
            online_transaction_complete_response.content,
            online_transaction_complete_expected_data
        )
        # _____________________________________#

        # Get transaction_details

        user_transaction_details_url = reverse(
            "v1:organization_transaction_detail",
            kwargs={"pk": transaction_id}
        )

        expected_user_transaction_info = {
            "id": transaction.id,
            "currency": "USD",
            "original_amount": 100.0,
            "discount_percent": 0,
            "savings": 10.0,
            "from_cashback": 0.0,
            "to_cashback": 0.0,
            "final_amount": 90.0,
            "processed_by": self.user.id,
            "employee_name": self.user.full_name,
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
            "employee_role": "Owner",
            "updated_at": transaction.updated_at.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "created_at": transaction.created_at.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "client": {
                "id": transaction.client.id,
                "full_name": transaction.client.full_name,
                "avatar": {
                    "id": transaction.client.avatar.id,
                    "file": f"http://testserver{transaction.client.avatar.file.url}",
                    "name": os.path.basename(
                        str(transaction.client.avatar.file)
                    ),
                    "large": f"http://testserver{transaction.client.avatar.large.url}",
                    "medium": f"http://testserver{transaction.client.avatar.medium.url}",
                    "small": f"http://testserver{transaction.client.avatar.small.url}",
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
                    "original_price": 100.0,
                    "discounted_price": 90.0
                },
                "items": [
                    {
                        "item": {
                            "id": item.id,
                            "name": item.name,
                            "price": 100.0,
                            "discounted_price": 90.0,
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
            "delivery_info": {
                "address": "Боконбаева",
                "apartment": None, "intercom": None, "entrance": None, "floor": None, "phone": "+996500441420",
                "comment": None},
        }
        user_transaction_details_response = self.client.get(
            user_transaction_details_url,
            content_type='application/json'
        )
        self.assertEqual(user_transaction_details_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_transaction_details_response.json(), expected_user_transaction_info)

        # Change shop item
        item_url = reverse(
            "v1:item_details",
            kwargs={"pk": item.id}
        )
        item_details_data = {
            "name": "Maasi",
            "organization": self.organization.id,
            "description": "Super cosy footwear. Keeps your legs warm in winter.",
            "price": 120.5,
            "discount": 10,
            "article": "123ART"
        }

        item_details_response = self.client.put(
            item_url,
            data=json.dumps(item_details_data),
            content_type='application/json'
        )
        self.assertEqual(item_details_response.status_code, status.HTTP_200_OK)

        # Check if transaction is not updated

        user_transaction_details_response = self.client.get(
            user_transaction_details_url,
            content_type='application/json'
        )
        self.assertEqual(user_transaction_details_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_transaction_details_response.json(), expected_user_transaction_info)

        # We are Reject the Transaction waiting that transaction fixed_cart will not change

        user_transaction_details_response = self.client.delete(
            user_transaction_details_url,
            content_type='application/json'
        )
        self.assertEqual(user_transaction_details_response.status_code, status.HTTP_204_NO_CONTENT)

        # Check transaction details. Waiting that it will not change

        expected_user_transaction_info = {
            "id": transaction.id,
            "currency": "USD",
            "original_amount": 100.0,
            "discount_percent": 0,
            "savings": 10.0,
            "from_cashback": 0.0,
            "to_cashback": 0.0,
            "final_amount": 90.0,
            "processed_by": self.user.id,
            "employee_name": self.user.full_name,
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
            "employee_role": "Owner",
            "updated_at": transaction.updated_at.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "created_at": transaction.created_at.strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
            "client": {
                "id": transaction.client.id,
                "full_name": transaction.client.full_name,
                "avatar": {
                    "id": transaction.client.avatar.id,
                    "file": f"http://testserver{transaction.client.avatar.file.url}",
                    "name": os.path.basename(
                        str(transaction.client.avatar.file)
                    ),
                    "large": f"http://testserver{transaction.client.avatar.large.url}",
                    "medium": f"http://testserver{transaction.client.avatar.medium.url}",
                    "small": f"http://testserver{transaction.client.avatar.small.url}",
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
                    "original_price": 100.0,
                    "discounted_price": 90.0
                },
                "items": [
                    {
                        "item": {
                            "id": item.id,
                            "name": item.name,
                            "price": 100.0,
                            "discounted_price": 90.0,
                            "image": {
                                "file": None,
                                "is_watermarked": False
                            }
                        },
                        "count": 1
                    }
                ]
            },
            "status": Transaction.REJECTED,
            "current_user_can_see_stats": True,
            "delivery_info": {
                "address": "Боконбаева",
                "apartment": None, "intercom": None, "entrance": None, "floor": None, "phone": "+996500441420",
                "comment": None},
        }

        user_transaction_details_response = self.client.get(
            user_transaction_details_url,
            content_type='application/json'
        )
        self.assertEqual(user_transaction_details_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_transaction_details_response.json(), expected_user_transaction_info)
