import json
import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.constants import MALE
from users.tests.factories import (
    UserFactory, )


class CurrentUserAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('v1:me')

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_current_user_data(self):
        user = UserFactory(
            full_name="Asadov Ahmed",
            username="Zoxon470",
            date_of_birth="1997-03-07",
            gender=MALE,
            email="zoxon470@gmail.com",
            phone_number="996550718131"
        )
        self.client.force_authenticate(user=user)
        expected_data = {
            "id": user.id,
            "full_name": user.full_name,
            "username": user.username,
            "date_of_birth": "1997-03-07",
            "gender": MALE,
            "email": user.email,
            "phone_number": user.phone_number,
            "avatar": {
                "id": user.avatar.id,
                "file": f"http://testserver{user.avatar.file.url}",
                "name": os.path.basename(user.avatar.file.name),
                "large": f"http://testserver{user.avatar.large.url}",
                "medium": f"http://testserver{user.avatar.medium.url}",
                "small": f"http://testserver{user.avatar.small.url}",
            }
        }

        response = self.client.get(
            self.url,
            content_type='application/json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
