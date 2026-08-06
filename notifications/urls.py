# notifications/api/urls.py
from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from notifications.views import NotificationViewSet

router = DefaultRouter()

router.register(
    "",
    NotificationViewSet,
    basename="notifications",
)
urlpatterns = [
    path(
        "",
        include(router.urls),
    ),
]