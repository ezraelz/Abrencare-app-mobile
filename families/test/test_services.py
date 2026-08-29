"""
Service-layer tests for the families app.

This is where the security-sensitive logic lives (token hashing,
OTP verification, invitation consumption, account-claim flow), so
it gets the deepest coverage.

`families.services` is a package (see families/services/__init__.py),
split into per-concern modules (crypto.py, verification.py,
acceptance.py, etc.) that are re-exported from the package root. Tests
call through the public `services.*` surface exactly as before -- the
one place that needs to know about the internal module layout is the
`generate_otp` patch target below, since `verification.py` imports
that function into its own namespace (`from .crypto import
generate_otp`) rather than looking it up on the package root at call
time. Patching `families.services.generate_otp` would only replace
the re-exported name in `__init__.py` and never reach the copy
`verification.py` actually calls, so we patch it where it's used.

Run with:
    python manage.py test families.tests.test_services
"""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from families import services
from families.models import (
    Family,
    FamilyMember,
    FamilyPatient,
    FamilyInvitation,
    InvitationDelivery,
)
from patients.models import Patient

User = get_user_model()

# `verification.py` binds `generate_otp` into its own module namespace
# via `from .crypto import generate_otp`, so that's what must be
# patched -- patching `families.services.generate_otp` (the
# package-root re-export) would not affect the call inside
# `request_invitation_contact_verification`.
GENERATE_OTP_PATCH_TARGET = "families.services.verification.generate_otp"


def make_user(username="user1", **kwargs):
    defaults = {"email": f"{username}@example.com"}
    defaults.update(kwargs)
    return User.objects.create_user(username=username, password="testpass123", **defaults)


def make_patient(user=None, **kwargs):
    if user is None:
        user = make_user(username=f"patientuser{Patient.objects.count()}")
    defaults = {"gender": "", "blood_group": ""}
    defaults.update(kwargs)
    return Patient.objects.create(user=user, **defaults)


def make_family(owner=None):
    owner = owner or make_user("familyowner")
    return services.create_family(user=owner, name="Test Family")


# ============================================================
# TOKEN / OTP HELPERS
# ============================================================

class TokenHelperTests(TestCase):
    def test_generate_invitation_token_returns_raw_and_hash(self):
        raw_token, token_hash = services.generate_invitation_token()
        self.assertTrue(raw_token)
        self.assertEqual(len(token_hash), 64)
        self.assertNotEqual(raw_token, token_hash)

    def test_hash_invitation_token_is_deterministic(self):
        raw_token, token_hash = services.generate_invitation_token()
        self.assertEqual(services.hash_invitation_token(raw_token), token_hash)

    def test_tokens_are_unique(self):
        raw_1, _ = services.generate_invitation_token()
        raw_2, _ = services.generate_invitation_token()
        self.assertNotEqual(raw_1, raw_2)


class OTPHelperTests(TestCase):
    def test_generate_otp_is_six_digits(self):
        otp = services.generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_hash_otp_round_trips(self):
        otp = services.generate_otp()
        self.assertEqual(services.hash_otp(otp), services.hash_otp(otp))
        self.assertNotEqual(services.hash_otp(otp), otp)


# ============================================================
# CREATE FAMILY
# ============================================================

class CreateFamilyTests(TestCase):
    def test_creates_family_and_owner_membership(self):
        user = make_user("creator")
        family = services.create_family(user=user, name="The Creators")

        self.assertEqual(family.created_by, user)
        member = FamilyMember.objects.get(family=family, user=user)
        self.assertEqual(member.role, FamilyMember.Role.OWNER)
        self.assertTrue(member.can_view_patient_records)
        self.assertTrue(member.can_manage_appointments)
        self.assertTrue(member.can_manage_medications)
        self.assertTrue(member.can_manage_family_members)
        self.assertTrue(member.can_manage_family_patients)


# ============================================================
# CREATE FAMILY PATIENT
# ============================================================

class CreateFamilyPatientTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.family = make_family(self.owner)

    def test_creates_new_user_and_patient_when_none_exist(self):
        family_patient = services.create_family_patient(
            family=self.family,
            created_by=self.owner,
            validated_data={
                "first_name": "New",
                "last_name": "Patient",
                "email": "newpatient@example.com",
            },
        )

        self.assertEqual(family_patient.family, self.family)
        new_user = family_patient.patient.user
        self.assertEqual(new_user.email, "newpatient@example.com")
        self.assertEqual(new_user.account_status, "pending")
        self.assertFalse(new_user.has_usable_password())

    def test_reuses_existing_user_found_by_email(self):
        existing_user = make_user("existing", email="existing@example.com")

        family_patient = services.create_family_patient(
            family=self.family,
            created_by=self.owner,
            validated_data={
                "first_name": "Existing",
                "email": "existing@example.com",
            },
        )

        self.assertEqual(family_patient.patient.user, existing_user)

    def test_reuses_existing_user_found_by_phone(self):
        existing_user = make_user("phoneuser", phone_number="+15551230000")

        family_patient = services.create_family_patient(
            family=self.family,
            created_by=self.owner,
            validated_data={
                "first_name": "Phone",
                "phone_number": "+15551230000",
            },
        )

        self.assertEqual(family_patient.patient.user, existing_user)

    def test_reuses_existing_patient_profile(self):
        existing_user = make_user("hasprofile", email="hasprofile@example.com")
        existing_patient = make_patient(user=existing_user)

        family_patient = services.create_family_patient(
            family=self.family,
            created_by=self.owner,
            validated_data={
                "first_name": "Has",
                "email": "hasprofile@example.com",
            },
        )

        self.assertEqual(family_patient.patient, existing_patient)
        self.assertEqual(Patient.objects.filter(user=existing_user).count(), 1)

    def test_duplicate_family_patient_raises_value_error(self):
        existing_user = make_user("dup", email="dup@example.com")
        make_patient(user=existing_user)

        services.create_family_patient(
            family=self.family,
            created_by=self.owner,
            validated_data={"first_name": "Dup", "email": "dup@example.com"},
        )

        with self.assertRaises(ValueError):
            services.create_family_patient(
                family=self.family,
                created_by=self.owner,
                validated_data={"first_name": "Dup", "email": "dup@example.com"},
            )


# ============================================================
# INVITE FAMILY MEMBER
# ============================================================

class InviteFamilyMemberTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner2")
        self.family = make_family(self.owner)

    def test_creates_invitation_and_returns_raw_token(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={
                "name": "Invitee",
                "email": "invitee@example.com",
                "role": FamilyMember.Role.MEMBER,
            },
        )

        self.assertTrue(raw_token)
        self.assertEqual(invitation.token_hash, services.hash_invitation_token(raw_token))
        self.assertEqual(invitation.status, FamilyInvitation.Status.PENDING)
        self.assertEqual(invitation.family, self.family)

    def test_raises_if_existing_user_already_a_member(self):
        existing_user = make_user("alreadymember", email="already@example.com")
        FamilyMember.objects.create(family=self.family, user=existing_user)

        with self.assertRaises(ValueError):
            services.invite_family_member(
                family=self.family,
                invited_by=self.owner,
                validated_data={"name": "Already", "email": "already@example.com"},
            )

    def test_cancels_previous_pending_invitation_for_same_contact(self):
        first_invitation, _ = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Invitee", "email": "repeat@example.com"},
        )

        services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Invitee Again", "email": "repeat@example.com"},
        )

        first_invitation.refresh_from_db()
        self.assertEqual(first_invitation.status, FamilyInvitation.Status.CANCELLED)

    def test_defaults_role_to_member_when_missing(self):
        invitation, _ = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "NoRole", "email": "norole@example.com"},
        )
        self.assertEqual(invitation.role, FamilyMember.Role.MEMBER)


# ============================================================
# PATIENT CLAIM INVITATION
# ============================================================

class CreatePatientClaimInvitationTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner3")
        self.family = make_family(self.owner)
        self.pending_user = make_user("pendingpatientuser", account_status="pending")
        self.patient = make_patient(user=self.pending_user)
        FamilyPatient.objects.create(family=self.family, patient=self.patient)

    def test_raises_without_patient(self):
        with self.assertRaises(ValueError):
            services.create_patient_claim_invitation(
                family=self.family,
                patient=None,
                invited_by=self.owner,
                validated_data={"email": "claim@example.com"},
            )

    def test_raises_if_patient_account_already_active(self):
        self.pending_user.account_status = "active"
        self.pending_user.save(update_fields=["account_status"])

        with self.assertRaises(ValueError):
            services.create_patient_claim_invitation(
                family=self.family,
                patient=self.patient,
                invited_by=self.owner,
                validated_data={"email": "claim@example.com"},
            )

    def test_raises_without_contact_info(self):
        with self.assertRaises(ValueError):
            services.create_patient_claim_invitation(
                family=self.family,
                patient=self.patient,
                invited_by=self.owner,
                validated_data={},
            )

    def test_creates_claim_invitation(self):
        invitation, raw_token = services.create_patient_claim_invitation(
            family=self.family,
            patient=self.patient,
            invited_by=self.owner,
            validated_data={"email": "claim@example.com"},
        )
        self.assertEqual(invitation.invitation_type, FamilyInvitation.InvitationType.PATIENT_CLAIM)
        self.assertEqual(invitation.patient, self.patient)
        self.assertTrue(raw_token)

    def test_cancels_previous_pending_claim_invitations(self):
        first_invitation, _ = services.create_patient_claim_invitation(
            family=self.family,
            patient=self.patient,
            invited_by=self.owner,
            validated_data={"email": "claim@example.com"},
        )

        services.create_patient_claim_invitation(
            family=self.family,
            patient=self.patient,
            invited_by=self.owner,
            validated_data={"email": "claim2@example.com"},
        )

        first_invitation.refresh_from_db()
        self.assertEqual(first_invitation.status, FamilyInvitation.Status.CANCELLED)


# ============================================================
# GET INVITATION BY TOKEN
# ============================================================

class GetInvitationByTokenTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner4")
        self.family = make_family(self.owner)

    def test_raises_for_empty_token(self):
        with self.assertRaises(ValueError):
            services.get_invitation_by_token("")

    def test_raises_for_unknown_token(self):
        with self.assertRaises(ValueError):
            services.get_invitation_by_token("does-not-exist")

    def test_returns_invitation_for_valid_pending_token(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Valid", "email": "valid@example.com"},
        )

        resolved = services.get_invitation_by_token(raw_token)
        self.assertEqual(resolved.id, invitation.id)

    def test_expired_invitation_raises_and_updates_status(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Expiring", "email": "expiring@example.com"},
        )
        FamilyInvitation.objects.filter(id=invitation.id).update(
            expires_at=timezone.now() - timedelta(days=1)
        )

        with self.assertRaises(ValueError):
            services.get_invitation_by_token(raw_token)

        invitation.refresh_from_db()
        self.assertEqual(invitation.status, FamilyInvitation.Status.EXPIRED)

    def test_non_pending_invitation_raises(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Cancelled", "email": "cancelled@example.com"},
        )
        invitation.status = FamilyInvitation.Status.CANCELLED
        invitation.save(update_fields=["status"])

        with self.assertRaises(ValueError):
            services.get_invitation_by_token(raw_token)


# ============================================================
# CONTACT VERIFICATION / OTP REQUEST
# ============================================================

class RequestInvitationContactVerificationTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner5")
        self.family = make_family(self.owner)

    def test_generates_otp_and_records_delivery(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Contact", "email": "contact@example.com"},
        )

        result = services.request_invitation_contact_verification(token=raw_token)

        invitation.refresh_from_db()
        self.assertTrue(invitation.otp_hash)
        self.assertIsNotNone(invitation.otp_expires_at)
        self.assertEqual(invitation.otp_attempts, 0)
        self.assertEqual(result["channel"], "email")
        self.assertTrue(InvitationDelivery.objects.filter(invitation=invitation).exists())

    def test_masks_email_destination(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Masked", "email": "masked@example.com"},
        )

        result = services.request_invitation_contact_verification(token=raw_token)

        self.assertNotEqual(result["destination"], "masked@example.com")
        self.assertIn("@example.com", result["destination"])
        self.assertIn("*", result["destination"])

    def test_masks_phone_destination(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "PhoneOnly", "phone_number": "+15559998888"},
        )

        result = services.request_invitation_contact_verification(token=raw_token)

        self.assertEqual(result["channel"], "sms")
        self.assertTrue(result["destination"].endswith("8888"))
        self.assertIn("*", result["destination"])

    def test_raises_if_invitation_not_pending(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "NotPending", "email": "notpending@example.com"},
        )
        invitation.status = FamilyInvitation.Status.ACCEPTED
        invitation.save(update_fields=["status"])

        with self.assertRaises(ValueError):
            services.request_invitation_contact_verification(token=raw_token)


class VerifyInvitationOTPTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner6")
        self.family = make_family(self.owner)
        self.invitation, self.raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "OTP Target", "email": "otp@example.com"},
        )

    def test_raises_if_no_otp_requested(self):
        with self.assertRaises(ValueError):
            services.verify_invitation_otp(token=self.raw_token, otp="123456")

    def _request_otp_and_get_plain_value(self):
        with mock.patch(GENERATE_OTP_PATCH_TARGET, return_value="654321"):
            services.request_invitation_contact_verification(token=self.raw_token)
        return "654321"

    def test_correct_otp_marks_contact_verified_and_clears_otp_fields(self):
        otp = self._request_otp_and_get_plain_value()

        result = services.verify_invitation_otp(token=self.raw_token, otp=otp)

        self.assertTrue(result["verified"])
        self.invitation.refresh_from_db()
        self.assertIsNotNone(self.invitation.contact_verified_at)
        self.assertEqual(self.invitation.otp_hash, "")
        self.assertIsNone(self.invitation.otp_expires_at)
        self.assertEqual(self.invitation.otp_attempts, 0)

    def test_incorrect_otp_raises_and_increments_attempts(self):
        self._request_otp_and_get_plain_value()

        with self.assertRaises(ValueError):
            services.verify_invitation_otp(token=self.raw_token, otp="000000")

        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.otp_attempts, 1)
        self.assertIsNone(self.invitation.contact_verified_at)

    def test_expired_otp_raises(self):
        self._request_otp_and_get_plain_value()
        FamilyInvitation.objects.filter(id=self.invitation.id).update(
            otp_expires_at=timezone.now() - timedelta(minutes=1)
        )

        with self.assertRaises(ValueError):
            services.verify_invitation_otp(token=self.raw_token, otp="654321")

    def test_max_attempts_exceeded_raises(self):
        self._request_otp_and_get_plain_value()
        FamilyInvitation.objects.filter(id=self.invitation.id).update(
            otp_attempts=services.verification.OTP_MAX_ATTEMPTS
        )

        with self.assertRaises(ValueError):
            services.verify_invitation_otp(token=self.raw_token, otp="654321")


# ============================================================
# ACCEPT INVITATION — EXISTING USER
# ============================================================

class AcceptInvitationTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner7")
        self.family = make_family(self.owner)

    def test_full_accept_flow(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Acceptor2", "email": "acceptor2@example.com"},
        )
        with mock.patch(GENERATE_OTP_PATCH_TARGET, return_value="222222"):
            services.request_invitation_contact_verification(token=raw_token)
        services.verify_invitation_otp(token=raw_token, otp="222222")

        user = make_user("acceptor2", email="acceptor2@example.com")
        member = services.accept_invitation(token=raw_token, user=user)

        self.assertEqual(member.family, self.family)
        self.assertEqual(member.user, user)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, FamilyInvitation.Status.ACCEPTED)
        self.assertIsNotNone(invitation.accepted_at)

    def test_raises_for_patient_claim_invitation_type(self):
        pending_user = make_user("claimowner", account_status="pending")
        patient = make_patient(user=pending_user)
        FamilyPatient.objects.create(family=self.family, patient=patient)
        invitation, raw_token = services.create_patient_claim_invitation(
            family=self.family,
            patient=patient,
            invited_by=self.owner,
            validated_data={"email": "claimtype@example.com"},
        )

        user = make_user("wrongtype")
        with self.assertRaises(ValueError):
            services.accept_invitation(token=raw_token, user=user)

    def test_raises_if_contact_not_verified(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Unverified", "email": "unverified@example.com"},
        )
        user = make_user("unverified", email="unverified@example.com")

        with self.assertRaises(ValueError):
            services.accept_invitation(token=raw_token, user=user)

    def test_raises_if_contact_does_not_match_user(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Mismatch", "email": "mismatch@example.com"},
        )
        with mock.patch(GENERATE_OTP_PATCH_TARGET, return_value="333333"):
            services.request_invitation_contact_verification(token=raw_token)
        services.verify_invitation_otp(token=raw_token, otp="333333")

        wrong_user = make_user("differentcontact", email="different@example.com")
        with self.assertRaises(ValueError):
            services.accept_invitation(token=raw_token, user=wrong_user)

    def test_raises_if_already_a_member(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "AlreadyIn", "email": "alreadyin@example.com"},
        )
        with mock.patch(GENERATE_OTP_PATCH_TARGET, return_value="444444"):
            services.request_invitation_contact_verification(token=raw_token)
        services.verify_invitation_otp(token=raw_token, otp="444444")

        user = make_user("alreadyin", email="alreadyin@example.com")
        FamilyMember.objects.create(family=self.family, user=user)

        with self.assertRaises(ValueError):
            services.accept_invitation(token=raw_token, user=user)


# ============================================================
# COMPLETE INVITATION REGISTRATION
# ============================================================

class CompleteInvitationRegistrationTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner8")
        self.family = make_family(self.owner)

    def _verified_invitation(self, email="newperson@example.com"):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "New Person", "email": email},
        )
        with mock.patch(GENERATE_OTP_PATCH_TARGET, return_value="555555"):
            services.request_invitation_contact_verification(token=raw_token)
        services.verify_invitation_otp(token=raw_token, otp="555555")
        return invitation, raw_token

    def test_creates_user_and_member(self):
        invitation, raw_token = self._verified_invitation()

        user, member = services.complete_invitation_registration(
            token=raw_token,
            validated_data={
                "first_name": "New",
                "last_name": "Person",
                "username": "newperson",
                "password": "strongpassword123",
            },
        )

        self.assertEqual(user.email, "newperson@example.com")
        self.assertTrue(user.check_password("strongpassword123"))
        self.assertEqual(user.account_status, "active")
        self.assertEqual(member.family, self.family)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, FamilyInvitation.Status.ACCEPTED)

    def test_raises_without_verification(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Unverified2", "email": "unverified2@example.com"},
        )

        with self.assertRaises(ValueError):
            services.complete_invitation_registration(
                token=raw_token,
                validated_data={"first_name": "X", "password": "strongpassword123"},
            )

    def test_raises_without_password(self):
        invitation, raw_token = self._verified_invitation(email="nopass@example.com")

        with self.assertRaises(ValueError):
            services.complete_invitation_registration(
                token=raw_token, validated_data={"first_name": "X"}
            )

    def test_raises_on_existing_email_account_collision(self):
        make_user("collider", email="collide@example.com")
        invitation, raw_token = self._verified_invitation(email="collide@example.com")

        with self.assertRaises(ValueError):
            services.complete_invitation_registration(
                token=raw_token,
                validated_data={"first_name": "X", "password": "strongpassword123"},
            )

    def test_raises_on_username_collision(self):
        make_user("takenusername")
        invitation, raw_token = self._verified_invitation(email="freeemail@example.com")

        with self.assertRaises(ValueError):
            services.complete_invitation_registration(
                token=raw_token,
                validated_data={
                    "first_name": "X",
                    "username": "takenusername",
                    "password": "strongpassword123",
                },
            )


# ============================================================
# COMPLETE PATIENT CLAIM
# ============================================================

class CompletePatientClaimTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner9")
        self.family = make_family(self.owner)
        self.pending_user = make_user(
            "claimant", email="claimant@example.com", account_status="pending"
        )
        self.patient = make_patient(user=self.pending_user)
        FamilyPatient.objects.create(family=self.family, patient=self.patient)

    def _verified_claim_invitation(self):
        invitation, raw_token = services.create_patient_claim_invitation(
            family=self.family,
            patient=self.patient,
            invited_by=self.owner,
            validated_data={"email": "claimant@example.com"},
        )
        with mock.patch(GENERATE_OTP_PATCH_TARGET, return_value="666666"):
            services.request_invitation_contact_verification(token=raw_token)
        services.verify_invitation_otp(token=raw_token, otp="666666")
        return invitation, raw_token

    def test_activates_existing_user_and_retains_patient(self):
        invitation, raw_token = self._verified_claim_invitation()

        user, patient = services.complete_patient_claim(
            token=raw_token,
            validated_data={"password": "strongpassword123"},
        )

        self.assertEqual(user.id, self.pending_user.id)
        self.assertEqual(patient.id, self.patient.id)
        self.assertEqual(user.account_status, "active")
        self.assertTrue(user.check_password("strongpassword123"))
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, FamilyInvitation.Status.ACCEPTED)

    def test_raises_for_member_invitation_type(self):
        invitation, raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "WrongType", "email": "wrongtype@example.com"},
        )
        with self.assertRaises(ValueError):
            services.complete_patient_claim(
                token=raw_token, validated_data={"password": "strongpassword123"}
            )

    def test_raises_without_verification(self):
        invitation, raw_token = services.create_patient_claim_invitation(
            family=self.family,
            patient=self.patient,
            invited_by=self.owner,
            validated_data={"email": "claimant@example.com"},
        )
        with self.assertRaises(ValueError):
            services.complete_patient_claim(
                token=raw_token, validated_data={"password": "strongpassword123"}
            )

    def test_raises_if_already_active(self):
        invitation, raw_token = self._verified_claim_invitation()
        self.pending_user.account_status = "active"
        self.pending_user.save(update_fields=["account_status"])

        with self.assertRaises(ValueError):
            services.complete_patient_claim(
                token=raw_token, validated_data={"password": "strongpassword123"}
            )

    def test_raises_without_password(self):
        invitation, raw_token = self._verified_claim_invitation()
        with self.assertRaises(ValueError):
            services.complete_patient_claim(token=raw_token, validated_data={})

    def test_raises_on_username_collision(self):
        make_user("takenclaimusername")
        invitation, raw_token = self._verified_claim_invitation()

        with self.assertRaises(ValueError):
            services.complete_patient_claim(
                token=raw_token,
                validated_data={
                    "username": "takenclaimusername",
                    "password": "strongpassword123",
                },
            )
            