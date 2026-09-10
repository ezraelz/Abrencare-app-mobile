# asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import notifications.routing
import chat.routing

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "Backend.settings"
)

# Initialize Django first
django_asgi_app = get_asgi_application()

# Import middleware after Django is ready
from notifications.middleware import JWTAuthMiddleware


application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": JWTAuthMiddleware(
        URLRouter(
            notifications.routing.websocket_urlpatterns
            + chat.routing.websocket_urlpatterns
        )
    ),
})