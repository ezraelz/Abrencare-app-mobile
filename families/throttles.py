# family/throttles.py

from rest_framework.throttling import AnonRateThrottle
from rest_framework.throttling import UserRateThrottle


class InvitationLookupThrottle(AnonRateThrottle):
    scope = "invitation_lookup"


class InvitationContactThrottle(AnonRateThrottle):
    scope = "invitation_contact"


class InvitationOTPThrottle(AnonRateThrottle):
    scope = "invitation_otp"


class InvitationRegistrationThrottle(AnonRateThrottle):
    scope = "invitation_registration"


class PatientClaimThrottle(AnonRateThrottle):
    scope = "patient_claim"


class FamilyInvitationCreateThrottle(UserRateThrottle):
    scope = "family_invitation_create"


class FamilyPatientCreateThrottle(UserRateThrottle):
    scope = "family_patient_create"
    