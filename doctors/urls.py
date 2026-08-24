from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    SpecialtyViewSet,
    DoctorView,
    DoctorDetailView,
    QualificationViewSet,
    DoctorAvailabilityViewSet,
)

urlpatterns = [
    path("doctors/", DoctorView.as_view(), name='doctors'),
    path("doctors/<int:pk>/", DoctorDetailView.as_view(), name='doctor-detail'),
    path("speciality/", SpecialtyViewSet.as_view({'get':'list'}), name='speciality'),
    path("availabity/", DoctorAvailabilityViewSet.as_view({'get': 'list'}), name='doctor-availabity'),
]
