from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FeatureViewSet,
    ServiceViewSet,
)

router = DefaultRouter()

router.register("features", FeatureViewSet)
router.register("services", ServiceViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
