from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import MyOwnToken
from django.utils import timezone

now = timezone.now()


class MyOwnTokenAuthentication(TokenAuthentication):
    model = MyOwnToken

    def authenticate_credentials(self, key):
        try:
            token = MyOwnToken.objects.get(key=key)
        except MyOwnToken.DoesNotExist:
            raise AuthenticationFailed("Invalid Token")

        if not token.user.is_active:
            raise AuthenticationFailed("User is not active")

        if token.expired_time < now:
            token.delete()
            raise AuthenticationFailed("The Token is expired")
        return (token.user, token)
