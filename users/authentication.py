from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from users.models import MyOwnToken
from django.utils import timezone




class MyOwnTokenAuthentication(TokenAuthentication):
    model = MyOwnToken

    def authenticate_credentials(self, key):
        now = timezone.now().replace(tzinfo=None)
        try:
            token = MyOwnToken.objects.get(key=key, is_active=True)
            token.last_active = now
            token.save()
        except MyOwnToken.DoesNotExist:
            raise AuthenticationFailed("Invalid Token")

        if not token.user.is_active:
            raise AuthenticationFailed("User is not active")
        if token.expired_time < now:
            token.is_active = False
            token.save()
            raise AuthenticationFailed("The Token is expired")
        return (token.user, token)
