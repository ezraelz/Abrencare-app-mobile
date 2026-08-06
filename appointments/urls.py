from django.urls import path, include

from .views import (
    AppointmentView,
    AppointmentDetailView,
    SchedulingView,
    SchedulingDetailView
)

urlpatterns = [
    path("appointments/", AppointmentView.as_view(), name='appointments'),
    path("appointments/<int:pk>/", AppointmentDetailView.as_view(), name='appointments-detail'),
    path("scheduling/", SchedulingView.as_view(), name='scheduling'),
    path("scheduling/<int:pk>/", SchedulingDetailView.as_view(), name='scheduling-detail')
]