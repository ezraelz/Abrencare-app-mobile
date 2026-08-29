from django.urls import path

from .views import (
    AppointmentListCreateView,
    AppointmentDetailView,
    AppointmentCancelView,
    AppointmentConfirmView,
    AppointmentCompleteView,
    AppointmentNoShowView,
    AppointmentRescheduleView
)


urlpatterns = [
    path("appointments/", AppointmentListCreateView.as_view(), name="appointment-list-create"),
    path("appointments/<int:pk>/", AppointmentDetailView.as_view(), name="appointment-detail"),
    path("appointments/<int:pk>/cancel/", AppointmentCancelView.as_view(), name="appointment-cancel"),
    path("appointments/<int:pk>/confirm/", AppointmentConfirmView.as_view(), name="appointment-confirm"),
    path("appointments/<int:pk>/complete/", AppointmentCompleteView.as_view(), name="appointment-complete"),
    path("appointments/<int:pk>/no-show/", AppointmentNoShowView.as_view(), name="appointment-no-show"),
    path("appointments/<int:pk>/reschedule/", AppointmentRescheduleView.as_view(), name="appointment-reschedule"),
]