# chat/middleware.py

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token):
    try:
        access_token = AccessToken(token)
        user_id = access_token["user_id"]
        return User.objects.get(id=user_id)
    except (TokenError, KeyError, User.DoesNotExist):
        return None


class JWTAuthMiddleware(BaseMiddleware):
    """
    Reads ?token=<access_token> from the WebSocket connection's query
    string and authenticates the scope, since browsers/RN can't set
    Authorization headers on a WebSocket handshake.
    """

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        token = parse_qs(query_string).get("token", [None])[0]

        scope["user"] = (
            await get_user_from_token(token) if token else None
        ) or AnonymousUser()

        return await super().__call__(scope, receive, send)
    