from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

User = get_user_model()


class UserManagerTestCase(APITestCase):
    def test_create_superuser(self):
        user = User.objects.create_superuser(
            "996550778133",
            "mypasswordnotfound"
        )
        self.assertIsNotNone(user.id)

    def test_create_user(self):
        user = User.objects.create_user(
            "996550778134",
            "mypasswordnotfound"
        )
        self.assertIsNotNone(user.id)

    def test_phone_number_is_required(self):
        with self.assertRaisesRegexp(
                ValueError, "User must have an phone_number address"):
            User.objects.create_superuser(
                None,
                "mypasswordnotfound"
            )
