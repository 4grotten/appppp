import json
import os
from datetime import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from common.tests.factories import FileFactory
from users.constants import MALE
from users.tests.factories import (
    UserFactory,
)


class ProfileInitialAPIViewTestCase(APITestCase):
    def setUp(self) -> None:
        self.url = reverse('v1:init_profile')

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

    def test_required_fields(self):
        user = UserFactory(phone_number="996550778131")
        self.client.force_authenticate(user=user)
        expected_data = {
            "message": "Invalid input",
            "errors": {
                "avatar_id": ["This field is required."],
                "gender": ["This field is required."]
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps({}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertJSONEqual(response.content, expected_data)

    def test_init_profile(self):
        user = UserFactory(email="zoxon470@gmail.com")
        avatar = FileFactory()
        self.client.force_authenticate(user=user)
        data = {
            "avatar_id": avatar.id,
            "username": "Zoxon470",
            "email": "zoxon470@gmail.com",
            "date_of_birth": datetime(1997, 3, 7).strftime("%Y-%m-%d"),
            "gender": MALE,
            "full_name": "Asadov Ahmed"
        }
        expected_data = {
            "id": user.id,
            "full_name": "Asadov Ahmed",
            "username": "Zoxon470",
            "date_of_birth": "1997-03-07",
            "gender": MALE,
            "email": "zoxon470@gmail.com",
            "phone_number": user.phone_number,
            "avatar": {
                "id": avatar.id,
                "file": f"http://testserver{avatar.file.url}",
                "name": os.path.basename(avatar.file.name),
                "large": f"http://testserver{avatar.large.url}",
                "medium": f"http://testserver{avatar.medium.url}",
                "small": f"http://testserver{avatar.small.url}",
            }
        }

        response = self.client.post(
            self.url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
