from django.urls import path

from .views import (
    SpecialtyListCreateView,
    SpecialtyDetailView,

    DoctorListCreateView,
    DoctorDetailView,
    DoctorMeView,
    DoctorDeactivateAccountView,

    DoctorApproveView,
    DoctorRejectView,
    DoctorSuspendView,

    QualificationListCreateView,
    QualificationDetailView,

    DoctorAvailabilityListCreateView,
    DoctorAvailabilityDetailView,
)


urlpatterns = [

    # ======================================================
    # SPECIALTIES
    # ======================================================

    path(
        "specialties/",
        SpecialtyListCreateView.as_view(),
        name="specialty-list-create",
    ),

    path(
        "specialties/<int:pk>/",
        SpecialtyDetailView.as_view(),
        name="specialty-detail",
    ),


    # ======================================================
    # DOCTORS
    # ======================================================

    path(
        "doctors/",
        DoctorListCreateView.as_view(),
        name="doctor-list-create",
    ),

    # IMPORTANT: "me" before <int:pk>
    path(
        "doctors/me/",
        DoctorMeView.as_view(),
        name="doctor-me",
    ),

    path(
        "doctors/me/deactivate/",
        DoctorDeactivateAccountView.as_view(),
        name="doctor-deactivate-account",
    ),

    path(
        "doctors/<int:pk>/",
        DoctorDetailView.as_view(),
        name="doctor-detail",
    ),


    # ======================================================
    # ADMIN APPROVAL
    # ======================================================

    path(
        "doctors/<int:pk>/approve/",
        DoctorApproveView.as_view(),
        name="doctor-approve",
    ),

    path(
        "doctors/<int:pk>/reject/",
        DoctorRejectView.as_view(),
        name="doctor-reject",
    ),

    path(
        "doctors/<int:pk>/suspend/",
        DoctorSuspendView.as_view(),
        name="doctor-suspend",
    ),


    # ======================================================
    # QUALIFICATIONS
    # ======================================================

    path(
        "doctors/<int:doctor_id>/qualifications/",
        QualificationListCreateView.as_view(),
        name="doctor-qualification-list-create",
    ),

    path(
        "doctors/<int:doctor_id>/qualifications/<int:pk>/",
        QualificationDetailView.as_view(),
        name="doctor-qualification-detail",
    ),


    # ======================================================
    # AVAILABILITY
    # ======================================================

    path(
        "doctors/<int:doctor_id>/availability/",
        DoctorAvailabilityListCreateView.as_view(),
        name="doctor-availability-list-create",
    ),

    path(
        "doctors/<int:doctor_id>/availability/<int:pk>/",
        DoctorAvailabilityDetailView.as_view(),
        name="doctor-availability-detail",
    ),
]
