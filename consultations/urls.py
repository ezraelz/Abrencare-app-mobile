from django.urls import path

from .views import (
    ConsultationBookingView,
    ConsultationCancelView,
    ConsultationCompleteView,
    ConsultationDetailView,
    ConsultationStartView,
    MyConsultationsView,
    PrescriptionCreateView,
)


urlpatterns = [
    path("", ConsultationBookingView.as_view(), name="book"),
    path("mine/", MyConsultationsView.as_view(), name="my-consultations"),
    path("<int:pk>/", ConsultationDetailView.as_view(), name="detail"),
    path("<int:pk>/cancel/", ConsultationCancelView.as_view(), name="cancel"),
    path("<int:pk>/start/", ConsultationStartView.as_view(), name="start"),
    path("<int:pk>/complete/", ConsultationCompleteView.as_view(), name="complete"),
    path("<int:pk>/prescriptions/", PrescriptionCreateView.as_view(), name="prescription-create"),
]