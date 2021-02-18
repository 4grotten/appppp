import json
from unittest import expectedFailure

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
    SocialNetworkContactFactory,
)


class UserSocialNetworksUpdateAPIViewTestCase(APITestCase):
    url_name = "v1:set_user_networks"

    def setUp(self) -> None:
        self.user = UserFactory(phone_number="996550979133")

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.post(
            reverse(self.url_name),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    @expectedFailure
    def test_update_user_social_networks(self):
        social_network_one = SocialNetworkContactFactory(user=self.user)
        social_network_two = SocialNetworkContactFactory(user=self.user)
        self.client.force_authenticate(user=self.user)
        data = {
            "networks": [
                "https://instagram.com/anettarakelyan/",
                "https://instagram.com/official.riley.reid.ig"
            ]
        }
        expected_data = {
            "message": "Successfully updated",
            "networks": [
                {
                    "id": social_network_one.id,
                    "url": "https://instagram.com/anettarakelyan/"
                },
                {
                    "id": social_network_two.id,
                    "url": "https://instagram.com/official.riley.reid.ig"
                },
            ]
        }

        response = self.client.post(
            reverse(self.url_name),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
