"""
View/integration tests for the families app.

These hit the real URLs and the real service layer (no mocking) so
they exercise permission checks, serializer validation, and the
service logic together the way a real client request would.

Run with:
    python manage.py test families.tests.test_views
"""
from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

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


def make_user(username, **kwargs):
    defaults = {"email": f"{username}@example.com"}
    defaults.update(kwargs)
    return User.objects.create_user(username=username, password="testpass123", **defaults)


def make_patient(user=None, **kwargs):
    if user is None:
        user = make_user(f"patientuser{Patient.objects.count()}")
    defaults = {"gender": "", "blood_group": ""}
    defaults.update(kwargs)
    return Patient.objects.create(user=user, **defaults)


# ============================================================
# FAMILY
# ============================================================

class FamilyListCreateViewTests(APITestCase):
    def setUp(self):
        self.user = make_user("alice")
        self.other_user = make_user("bob")
        self.family = services.create_family(user=self.user, name="Alice Family")
        self.url = reverse("family-list-create")

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_returns_only_own_families(self):
        services.create_family(user=self.other_user, name="Bob Family")

        self.client.force_authenticate(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [f["name"] for f in response.data]
        self.assertIn("Alice Family", names)
        self.assertNotIn("Bob Family", names)

    def test_create_family_makes_creator_owner(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {"name": "New Family"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        family = Family.objects.get(id=response.data["id"])
        member = FamilyMember.objects.get(family=family, user=self.user)
        self.assertEqual(member.role, FamilyMember.Role.OWNER)

    def test_create_family_missing_name_is_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_family_blank_name_is_rejected(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {"name": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FamilyDetailViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner")
        self.outsider = make_user("outsider")
        self.family = services.create_family(user=self.owner, name="Detail Family")
        self.url = reverse("family-detail", kwargs={"family_id": self.family.id})

    def test_member_can_retrieve_family(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Detail Family")

    def test_non_member_forbidden(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unknown_family_returns_403_via_permission_check(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(reverse("family-detail", kwargs={"family_id": 999999}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_member_can_patch_name(self):
        self.client.force_authenticate(self.owner)
        response = self.client.patch(self.url, {"name": "Renamed"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.family.refresh_from_db()
        self.assertEqual(self.family.name, "Renamed")


# ============================================================
# FAMILY MEMBERS
# ============================================================

class FamilyMemberListViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner2")
        self.outsider = make_user("outsider2")
        self.family = services.create_family(user=self.owner, name="Members Family")
        member_user = make_user("member2")
        FamilyMember.objects.create(family=self.family, user=member_user)
        self.url = reverse("family-member-list", kwargs={"family_id": self.family.id})

    def test_member_can_list_members(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_non_member_forbidden(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ============================================================
# FAMILY PATIENTS
# ============================================================

class FamilyPatientListAndDetailViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner3")
        self.outsider = make_user("outsider3")
        self.family = services.create_family(user=self.owner, name="Patients Family")
        self.patient = make_patient()
        self.family_patient = FamilyPatient.objects.create(
            family=self.family, patient=self.patient, is_primary=True
        )
        self.list_url = reverse("family-patient-list", kwargs={"family_id": self.family.id})
        self.detail_url = reverse(
            "family-patient-detail",
            kwargs={"family_id": self.family.id, "patient_id": self.patient.id},
        )

    def test_list_patients(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_retrieve_patient_detail_excludes_medical_records(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("medical_records", response.data)

    def test_detail_unknown_patient_404(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(
            reverse(
                "family-patient-detail",
                kwargs={"family_id": self.family.id, "patient_id": 999999},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_non_member_forbidden(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FamilyPatientCreateViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner4")
        self.plain_member = make_user("plainmember4")
        self.family = services.create_family(user=self.owner, name="Create Family")
        FamilyMember.objects.create(family=self.family, user=self.plain_member)
        self.url = reverse("family-patient-create", kwargs={"family_id": self.family.id})

    def test_owner_can_create_family_patient(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "first_name": "New",
            "last_name": "Patient",
            "email": "newfamilypatient@example.com",
        }
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            FamilyPatient.objects.filter(
                family=self.family, patient__user__email="newfamilypatient@example.com"
            ).exists()
        )

    def test_member_without_manage_patients_permission_forbidden(self):
        self.client.force_authenticate(self.plain_member)
        response = self.client.post(
            self.url,
            {"first_name": "Nope", "email": "nope@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_missing_contact_info_returns_400(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.url, {"first_name": "NoContact"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_family_patient_returns_400(self):
        self.client.force_authenticate(self.owner)
        payload = {"first_name": "Dup", "email": "dupviewpatient@example.com"}
        self.client.post(self.url, payload, format="json")
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)


# ============================================================
# FAMILY MEMBER INVITATION
# ============================================================

class FamilyMemberInvitationCreateViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner5")
        self.plain_member = make_user("plainmember5")
        self.family = services.create_family(user=self.owner, name="Invite Family")
        FamilyMember.objects.create(family=self.family, user=self.plain_member)
        self.url = reverse(
            "family-member-invitation-create", kwargs={"family_id": self.family.id}
        )

    def test_create_invitation_returns_201_and_never_leaks_raw_token(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.url,
            {
                "name": "Invitee",
                "email": "invitee@example.com",
                "role": FamilyMember.Role.MEMBER,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        invitation = FamilyInvitation.objects.get(id=response.data["id"])
        self.assertNotIn("token", response.data)
        self.assertNotIn(invitation.token_hash, str(response.data))

    def test_member_without_manage_members_permission_forbidden(self):
        self.client.force_authenticate(self.plain_member)
        response = self.client.post(
            self.url, {"name": "Nope", "email": "nope5@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_existing_member_contact_returns_400(self):
        existing = make_user("existingmember5", email="existing5@example.com")
        FamilyMember.objects.create(family=self.family, user=existing)

        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.url, {"name": "Existing", "email": "existing5@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_contact_returns_400(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(self.url, {"name": "NoContact"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================
# PATIENT CLAIM INVITATION
# ============================================================

class PatientClaimInvitationCreateViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner6")
        self.family = services.create_family(user=self.owner, name="Claim Family")
        self.pending_user = make_user(
            "claimtarget6", email="claimtarget6@example.com", account_status="pending"
        )
        self.patient = make_patient(user=self.pending_user)
        FamilyPatient.objects.create(family=self.family, patient=self.patient)
        self.url = reverse(
            "patient-claim-invitation-create",
            kwargs={"family_id": self.family.id, "patient_id": self.patient.id},
        )

    def test_creates_claim_invitation(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.url, {"email": "claimtarget6@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data["invitation_type"], FamilyInvitation.InvitationType.PATIENT_CLAIM
        )

    def test_already_active_patient_returns_400(self):
        self.pending_user.account_status = "active"
        self.pending_user.save(update_fields=["account_status"])

        self.client.force_authenticate(self.owner)
        response = self.client.post(
            self.url, {"email": "claimtarget6@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_patient_in_family_returns_404(self):
        self.client.force_authenticate(self.owner)
        response = self.client.post(
            reverse(
                "patient-claim-invitation-create",
                kwargs={"family_id": self.family.id, "patient_id": 999999},
            ),
            {"email": "x@example.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================
# PUBLIC INVITATION ENDPOINTS (AllowAny)
# ============================================================

class InvitationDetailViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner7")
        self.family = services.create_family(user=self.owner, name="Lookup Family")
        self.invitation, self.raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Looked Up", "email": "lookedup@example.com"},
        )

    def test_valid_token_is_public_and_returns_invitation(self):
        url = reverse("invitation-detail", kwargs={"token": self.raw_token})
        response = self.client.get(url)  # no auth

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["valid"])
        self.assertEqual(response.data["invitation"]["id"], self.invitation.id)

    def test_invalid_token_returns_404_with_valid_false(self):
        url = reverse("invitation-detail", kwargs={"token": "not-a-real-token"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data["valid"])


class InvitationContactVerificationViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner8")
        self.family = services.create_family(user=self.owner, name="Verify Family")
        self.invitation, self.raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Verify Target", "email": "verifytarget@example.com"},
        )

    def test_triggers_otp_delivery_and_masks_destination(self):
        url = reverse("invitation-verify-contact", kwargs={"token": self.raw_token})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["channel"], "email")
        self.assertIn("*", response.data["destination"])
        self.assertTrue(
            InvitationDelivery.objects.filter(invitation=self.invitation).exists()
        )

    def test_invalid_token_returns_400(self):
        url = reverse("invitation-verify-contact", kwargs={"token": "bad-token"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class InvitationOTPVerificationViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner9")
        self.family = services.create_family(user=self.owner, name="OTP Family")
        self.invitation, self.raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "OTP Target", "email": "otptarget@example.com"},
        )
        self.url = reverse("invitation-verify-otp", kwargs={"token": self.raw_token})

    def test_correct_otp_succeeds(self):
        with mock.patch("families.services.generate_otp", return_value="123456"):
            self.client.post(
                reverse("invitation-verify-contact", kwargs={"token": self.raw_token})
            )

        response = self.client.post(self.url, {"otp": "123456"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["verified"])

    def test_incorrect_otp_returns_400(self):
        self.client.post(
            reverse("invitation-verify-contact", kwargs={"token": self.raw_token})
        )
        response = self.client.post(self.url, {"otp": "000000"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_digit_otp_is_rejected_by_serializer(self):
        response = self.client.post(self.url, {"otp": "abcdef"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_otp_field_is_rejected(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================
# ACCEPT INVITATION — EXISTING USER
# ============================================================

class InvitationAcceptViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner10")
        self.family = services.create_family(user=self.owner, name="Accept Family")
        self.invitation, self.raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Acceptor", "email": "acceptor10@example.com"},
        )
        self.url = reverse("invitation-accept", kwargs={"token": self.raw_token})
        self.user = make_user("acceptor10", email="acceptor10@example.com")

    def test_requires_authentication(self):
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def _verify_contact(self):
        with mock.patch("families.services.generate_otp", return_value="999999"):
            self.client.post(
                reverse("invitation-verify-contact", kwargs={"token": self.raw_token})
            )
        self.client.post(
            reverse("invitation-verify-otp", kwargs={"token": self.raw_token}),
            {"otp": "999999"},
            format="json",
        )

    def test_authenticated_user_can_accept_after_verification(self):
        self._verify_contact()
        self.client.force_authenticate(self.user)

        response = self.client.post(self.url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            FamilyMember.objects.filter(family=self.family, user=self.user).exists()
        )

    def test_accept_without_verification_returns_400(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accept_requires_confirm_true(self):
        self._verify_contact()
        self.client.force_authenticate(self.user)
        response = self.client.post(self.url, {"confirm": False}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================
# COMPLETE INVITATION REGISTRATION
# ============================================================

class InvitationRegistrationViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner11")
        self.family = services.create_family(user=self.owner, name="Register Family")
        self.invitation, self.raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "New Person", "email": "newperson11@example.com"},
        )
        self.url = reverse("invitation-register", kwargs={"token": self.raw_token})

    def _verify_contact(self):
        with mock.patch("families.services.generate_otp", return_value="121212"):
            self.client.post(
                reverse("invitation-verify-contact", kwargs={"token": self.raw_token})
            )
        self.client.post(
            reverse("invitation-verify-otp", kwargs={"token": self.raw_token}),
            {"otp": "121212"},
            format="json",
        )

    def test_public_registration_creates_user_and_member(self):
        self._verify_contact()

        response = self.client.post(
            self.url,
            {
                "first_name": "New",
                "last_name": "Person",
                "username": "newperson11",
                "password": "strongpassword123",
                "password_confirmation": "strongpassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("family_member", response.data)
        self.assertNotIn("password", response.data["user"])

    def test_password_mismatch_returns_400(self):
        self._verify_contact()
        response = self.client.post(
            self.url,
            {
                "first_name": "New",
                "password": "strongpassword123",
                "password_confirmation": "differentpassword",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_without_verification_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "New",
                "password": "strongpassword123",
                "password_confirmation": "strongpassword123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================
# COMPLETE PATIENT CLAIM
# ============================================================

class PatientClaimCompletionViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner12")
        self.family = services.create_family(user=self.owner, name="Claim Complete Family")
        self.pending_user = make_user(
            "claimant12", email="claimant12@example.com", account_status="pending"
        )
        self.patient = make_patient(user=self.pending_user)
        FamilyPatient.objects.create(family=self.family, patient=self.patient)
        self.invitation, self.raw_token = services.create_patient_claim_invitation(
            family=self.family,
            patient=self.patient,
            invited_by=self.owner,
            validated_data={"email": "claimant12@example.com"},
        )
        self.url = reverse("patient-claim-complete", kwargs={"token": self.raw_token})

    def _verify_contact(self):
        with mock.patch("families.services.generate_otp", return_value="343434"):
            self.client.post(
                reverse("invitation-verify-contact", kwargs={"token": self.raw_token})
            )
        self.client.post(
            reverse("invitation-verify-otp", kwargs={"token": self.raw_token}),
            {"otp": "343434"},
            format="json",
        )

    def test_completes_claim_and_retains_patient(self):
        self._verify_contact()

        response = self.client.post(
            self.url,
            {
                "first_name": "Claimant",
                "password": "strongpassword123",
                "password_confirmation": "strongpassword123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["patient"]["id"], self.patient.id)
        self.assertEqual(response.data["user"]["id"], self.pending_user.id)
        self.assertNotIn("password", response.data["user"])

    def test_claim_without_verification_returns_400(self):
        response = self.client.post(
            self.url,
            {
                "first_name": "Claimant",
                "password": "strongpassword123",
                "password_confirmation": "strongpassword123",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ============================================================
# INVITATION DELIVERY HISTORY
# ============================================================

class InvitationDeliveryListViewTests(APITestCase):
    def setUp(self):
        self.owner = make_user("owner13")
        self.outsider = make_user("outsider13")
        self.family = services.create_family(user=self.owner, name="Delivery Family")
        self.invitation, self.raw_token = services.invite_family_member(
            family=self.family,
            invited_by=self.owner,
            validated_data={"name": "Delivery Target", "email": "deliverytarget13@example.com"},
        )
        services.request_invitation_contact_verification(token=self.raw_token)
        self.url = reverse(
            "invitation-delivery-list",
            kwargs={"family_id": self.family.id, "invitation_id": self.invitation.id},
        )

    def test_requires_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_family_member_can_view_deliveries(self):
        self.client.force_authenticate(self.owner)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_invitation_from_wrong_family_returns_404(self):
        other_family = services.create_family(user=self.outsider, name="Other Family")

        self.client.force_authenticate(self.outsider)
        response = self.client.get(
            reverse(
                "invitation-delivery-list",
                kwargs={"family_id": other_family.id, "invitation_id": self.invitation.id},
            )
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_KNOWN_GAP_non_member_with_correct_ids_can_view_deliveries(self):
        """
        InvitationDeliveryListView only declares IsAuthenticated, not
        IsFamilyMember (unlike every other family-scoped view in this
        module). Any authenticated user who knows a valid family_id +
        invitation_id pair for someone else's family currently gets a
        200, not a 403. This test documents that as current behavior;
        it's worth confirming with the team whether IsFamilyMember
        should be added to this view's permission_classes.
        """
        self.client.force_authenticate(self.outsider)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
