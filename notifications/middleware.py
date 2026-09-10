# notifications/middleware.py
from urllib.parse import parse_qs
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.exceptions import AuthenticationFailed

class JWTAuthMiddleware:
    """
    Authenticate websocket connections using a JWT supplied as:

        ws://localhost:8000/ws/notifications/?token=<access_token>
    """

    def __init__(self, inner):
        self.inner = inner
        self.jwt_auth = JWTAuthentication()

    async def __call__(self, scope, receive, send):
        scope["user"] = AnonymousUser()
        scope["token"] = None

        query_string = scope.get("query_string", b"").decode()

        params = parse_qs(query_string)

        raw_token = params.get("token")

        if raw_token:
            try:
                validated_token = self.jwt_auth.get_validated_token(raw_token[0])

                user = await database_sync_to_async(
                    self.jwt_auth.get_user
                )(validated_token)

                scope["user"] = user
                scope["token"] = validated_token

            except (InvalidToken, TokenError, AuthenticationFailed) as exc:
                print("WS auth failed:", exc)  # temporary, remove after debugging

        return await self.inner(scope, receive, send)
    