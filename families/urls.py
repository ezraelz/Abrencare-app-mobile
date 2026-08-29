from django.urls import path

from .views import (
    FamilyListCreateView,
    FamilyDetailView,

    FamilyMemberListView,

    FamilyPatientListView,
    FamilyPatientDetailView,
    FamilyPatientCreateView,

    FamilyMemberInvitationCreateView,
    PatientClaimInvitationCreateView,

    InvitationDetailView,
    InvitationContactVerificationView,
    InvitationOTPVerificationView,
    InvitationAcceptView,
    InvitationRegistrationView,
    PatientClaimCompletionView,

    InvitationDeliveryListView,
)


urlpatterns = [

    # ========================================================
    # FAMILY
    # ========================================================

    path(
        "families/",
        FamilyListCreateView.as_view(),
        name="family-list-create",
    ),

    path(
        "families/<int:family_id>/",
        FamilyDetailView.as_view(),
        name="family-detail",
    ),


    # ========================================================
    # FAMILY MEMBERS
    # ========================================================

    path(
        "families/<int:family_id>/members/",
        FamilyMemberListView.as_view(),
        name="family-member-list",
    ),


    # ========================================================
    # FAMILY PATIENTS
    # ========================================================

    path(
        "families/<int:family_id>/patients/",
        FamilyPatientListView.as_view(),
        name="family-patient-list",
    ),

    path(
        "families/<int:family_id>/patients/create/",
        FamilyPatientCreateView.as_view(),
        name="family-patient-create",
    ),

    path(
        "families/<int:family_id>/patients/<int:patient_id>/",
        FamilyPatientDetailView.as_view(),
        name="family-patient-detail",
    ),


    # ========================================================
    # FAMILY MEMBER INVITATIONS
    # ========================================================

    path(
        "families/<int:family_id>/invitations/members/",
        FamilyMemberInvitationCreateView.as_view(),
        name="family-member-invitation-create",
    ),


    # ========================================================
    # PATIENT CLAIM INVITATIONS
    # ========================================================

    path(
        "families/<int:family_id>/patients/"
        "<int:patient_id>/claim-invitation/",
        PatientClaimInvitationCreateView.as_view(),
        name="patient-claim-invitation-create",
    ),


    # ========================================================
    # INVITATION
    # ========================================================

    path(
        "invitations/<str:token>/",
        InvitationDetailView.as_view(),
        name="invitation-detail",
    ),

    path(
        "invitations/<str:token>/verify-contact/",
        InvitationContactVerificationView.as_view(),
        name="invitation-verify-contact",
    ),

    path(
        "invitations/<str:token>/verify-otp/",
        InvitationOTPVerificationView.as_view(),
        name="invitation-verify-otp",
    ),

    path(
        "invitations/<str:token>/accept/",
        InvitationAcceptView.as_view(),
        name="invitation-accept",
    ),

    path(
        "invitations/<str:token>/register/",
        InvitationRegistrationView.as_view(),
        name="invitation-register",
    ),

    path(
        "invitations/<str:token>/claim-patient/",
        PatientClaimCompletionView.as_view(),
        name="patient-claim-complete",
    ),


    # ========================================================
    # INVITATION DELIVERY
    # ========================================================

    path(
        "families/<int:family_id>/invitations/"
        "<int:invitation_id>/deliveries/",
        InvitationDeliveryListView.as_view(),
        name="invitation-delivery-list",
    ),
]
