import json
import os
from datetime import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.constants import MALE
from users.tests.factories import (
    UserFactory,
    TokenFactory
)


class LoginAPIViewTestCase(APITestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.url = reverse('v1:login')

    def test_required_fields(self):
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "phone_number": ["This field is required."],
                "password": ["This field is required."],
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_wrong_credentials(self):
        UserFactory(phone_number="996550778333")
        data = {
            "phone_number": "996550000001",
            "password": "mypasswordnotfound"
        }
        expected_data = {
            "message": "Wrong credentials",
            "errors": {}
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertJSONEqual(response.content, expected_data)

    def test_user_logged_in(self):
        user = UserFactory(
            full_name="Asadov Ahmed",
            username="Zoxon470",
            date_of_birth=datetime(1997, 3, 7).strftime("%Y-%m-%d"),
            email="zoxon470@gmail.com",
            gender=MALE,
            phone_number="996550778333",
        )
        user.set_password('mypasswordnotfound')
        user.save(update_fields=['password'])
        token = TokenFactory(user=user)
        data = {
            "phone_number": str(user.phone_number),
            "password": "mypasswordnotfound"
        }
        expected_data = {
            "message": "Successfully logged in",
            "token": token.key,
            "user": {
                "id": user.id,
                "username": user.username,
                "date_of_birth": user.date_of_birth,
                "email": user.email,
                "full_name": user.full_name,
                "gender": user.gender,
                "phone_number": str(user.phone_number),
                "avatar": {
                    "id": user.avatar.id,
                    "file": f"http://testserver{user.avatar.file.url}",
                    "name": os.path.basename(user.avatar.file.name),
                    "large": f"http://testserver{user.avatar.large.url}",
                    "medium": f"http://testserver{user.avatar.medium.url}",
                    "small": f"http://testserver{user.avatar.small.url}",
                }
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
