from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests.factories import (
    UserFactory,
    SocialNetworkContactFactory,
)


class UserSocialNetworksListAPIViewTestCase(APITestCase):
    url_name = "v1:user_networks"

    def setUp(self) -> None:
        self.user = UserFactory(phone_number="996550979133")

    def test_user_unauthorized(self):
        expected_data = {
            "detail": "Authentication credentials were not provided."
        }

        response = self.client.get(
            reverse(self.url_name, kwargs={"pk": self.user.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertJSONEqual(response.content, expected_data)

    def test_get_user_social_networks_list(self):
        social_network_one = SocialNetworkContactFactory(user=self.user)
        social_network_two = SocialNetworkContactFactory(user=self.user)
        self.client.force_authenticate(user=self.user)
        expected_data = [
            {
                "id": social_network_one.id,
                "url": social_network_one.url
            },
            {
                "id": social_network_two.id,
                "url": social_network_two.url
            },
        ]

        response = self.client.get(
            reverse(self.url_name, kwargs={"pk": self.user.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertJSONEqual(response.content, expected_data)
