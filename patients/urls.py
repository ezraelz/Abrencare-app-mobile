from django.urls import path

from .views import (
    PatientMeView,
    PatientDetailView,
    PatientDeactivateAccountView,

    EmergencyContactListCreateView,
    EmergencyContactDetailView,

    PatientMedicalRecordListView,
    PatientMedicalRecordDetailView,

    PatientMedicalDocumentListCreateView,
    PatientMedicalDocumentDetailView,
    PatientMedicalDocumentReplaceView
)


urlpatterns = [

    # ==================================================
    # CURRENT PATIENT
    # ==================================================

    path(
        "me/",
        PatientMeView.as_view(),
        name="patient-me",
    ),

    path(
        "me/deactivate/",
        PatientDeactivateAccountView.as_view(),
        name="patient-deactivate-account",
    ),


    # ==================================================
    # PATIENT
    # ==================================================

    path(
        "<int:pk>/",
        PatientDetailView.as_view(),
        name="patient-detail",
    ),


    # ==================================================
    # EMERGENCY CONTACTS
    # ==================================================

    path(
        "me/emergency-contacts/",
        EmergencyContactListCreateView.as_view(),
        name="my-emergency-contact-list-create",
    ),

    path(
        "me/emergency-contacts/<int:pk>/",
        EmergencyContactDetailView.as_view(),
        name="my-emergency-contact-detail",
    ),


    # ==================================================
    # MEDICAL RECORDS
    # ==================================================

    path(
        "me/medical-records/",
        PatientMedicalRecordListView.as_view(),
        name="patient-medical-record-list",
    ),

    path(
        "me/medical-records/<int:pk>/",
        PatientMedicalRecordDetailView.as_view(),
        name="patient-medical-record-detail",
    ),


    # ==================================================
    # MEDICAL DOCUMENTS
    # ==================================================

    path(
        "me/medical-documents/",
        PatientMedicalDocumentListCreateView.as_view(),
        name="patient-medical-document-list-create",
    ),

    path(
        "me/medical-documents/<int:pk>/",
        PatientMedicalDocumentDetailView.as_view(),
        name="patient-medical-document-detail",
    ),
    path(
        "me/medical-documents/<int:pk>/replace/",
        PatientMedicalDocumentReplaceView.as_view(),
        name="patient-medical-document-replace",
    ),
]