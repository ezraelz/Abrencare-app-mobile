from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    SpecialtyViewSet,
    DoctorViewSet,
    QualificationViewSet,
    DoctorAvailabilityViewSet,
)

router = DefaultRouter()
router.register("specialties", SpecialtyViewSet)
router.register("doctors", DoctorViewSet)
router.register("qualifications", QualificationViewSet)
router.register("availability", DoctorAvailabilityViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
