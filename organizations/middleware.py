from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework.exceptions import AuthenticationFailed

from users.authentication import MyOwnTokenAuthentication


@database_sync_to_async
def get_user_from_token(token_key):
    try:
        user, token = MyOwnTokenAuthentication().authenticate_credentials(token_key)
        return user
    except AuthenticationFailed:
        return AnonymousUser()


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        token_key = headers.get(b'sec-websocket-protocol')

        if token_key:
            scope['user'] = await get_user_from_token(token_key.decode())
            scope['subprotocol'] = token_key.decode()
        else:
            scope['user'] = AnonymousUser()

        close_old_connections()
        return await super().__call__(scope, receive, send)

