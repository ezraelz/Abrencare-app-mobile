from django.urls import include, path

from .views import (
    PatientView,
    PatientDetailView,
    MedicalRecordViewSet,
    MedicalDocumentViewSet,
)

urlpatterns = [
    path("patients/", PatientView.as_view(), name='patients'),
    path("patients/<int:pk>/", PatientDetailView.as_view(), name='patient-detail'),
]
