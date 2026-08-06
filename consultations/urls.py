from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ConsultationViewSet,
    PrescriptionViewSet,
)

router = DefaultRouter()

router.register("consultations", ConsultationViewSet)
router.register("prescriptions", PrescriptionViewSet)

urlpatterns = [
    path("", include(router.urls)),
]