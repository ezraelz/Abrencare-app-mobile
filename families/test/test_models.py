"""
Model tests for the families app.

Run with:
    python manage.py test families.tests.test_models
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from families.models import (
    Family,
    FamilyMember,
    FamilyPatient,
    FamilyInvitation,
    InvitationDelivery,
)
from patients.models import Patient

User = get_user_model()


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


class FamilyModelTests(TestCase):
    def test_str_returns_name(self):
        owner = make_user("owner1")
        family = Family.objects.create(name="The Does", created_by=owner)
        self.assertEqual(str(family), "The Does")

    def test_ordering_is_by_name(self):
        owner = make_user("owner2")
        Family.objects.create(name="Zeta", created_by=owner)
        Family.objects.create(name="Alpha", created_by=owner)
        names = list(Family.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))

    def test_created_by_protected_on_delete(self):
        owner = make_user("owner3")
        Family.objects.create(name="Protected Family", created_by=owner)
        with self.assertRaises(Exception):
            owner.delete()


class FamilyMemberModelTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner4")
        self.family = Family.objects.create(name="Test Family", created_by=self.owner)

    def test_str_representation(self):
        member = FamilyMember.objects.create(
            family=self.family, user=self.owner, role=FamilyMember.Role.OWNER
        )
        self.assertIn(str(self.owner), str(member))
        self.assertIn(str(self.family), str(member))

    def test_default_permission_flags_are_false(self):
        member = FamilyMember.objects.create(family=self.family, user=self.owner)
        self.assertFalse(member.can_view_patient_records)
        self.assertFalse(member.can_manage_appointments)
        self.assertFalse(member.can_manage_medications)
        self.assertFalse(member.can_manage_family_members)
        self.assertFalse(member.can_manage_family_patients)

    def test_default_role_is_member(self):
        member = FamilyMember.objects.create(family=self.family, user=self.owner)
        self.assertEqual(member.role, FamilyMember.Role.MEMBER)

    def test_unique_family_user_constraint(self):
        FamilyMember.objects.create(family=self.family, user=self.owner)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FamilyMember.objects.create(family=self.family, user=self.owner)

    def test_only_one_owner_per_family(self):
        FamilyMember.objects.create(
            family=self.family, user=self.owner, role=FamilyMember.Role.OWNER
        )
        second_user = make_user("member1")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FamilyMember.objects.create(
                    family=self.family, user=second_user, role=FamilyMember.Role.OWNER
                )

    def test_multiple_non_owner_members_allowed(self):
        FamilyMember.objects.create(
            family=self.family, user=self.owner, role=FamilyMember.Role.OWNER
        )
        member_user = make_user("member2")
        caregiver_user = make_user("caregiver1")
        FamilyMember.objects.create(
            family=self.family, user=member_user, role=FamilyMember.Role.MEMBER
        )
        FamilyMember.objects.create(
            family=self.family, user=caregiver_user, role=FamilyMember.Role.CAREGIVER
        )
        self.assertEqual(self.family.members.count(), 3)

    def test_same_user_can_belong_to_multiple_families(self):
        other_family = Family.objects.create(name="Other Family", created_by=self.owner)
        FamilyMember.objects.create(family=self.family, user=self.owner)
        FamilyMember.objects.create(family=other_family, user=self.owner)
        self.assertEqual(self.owner.family_memberships.count(), 2)


class FamilyPatientModelTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner5")
        self.family = Family.objects.create(name="Patient Family", created_by=self.owner)
        self.patient = make_patient()

    def test_str_representation(self):
        fp = FamilyPatient.objects.create(family=self.family, patient=self.patient)
        self.assertIn(str(self.patient), str(fp))
        self.assertIn(str(self.family), str(fp))

    def test_default_relationship_is_other(self):
        fp = FamilyPatient.objects.create(family=self.family, patient=self.patient)
        self.assertEqual(fp.relationship, FamilyPatient.Relationship.OTHER)

    def test_default_is_primary_false(self):
        fp = FamilyPatient.objects.create(family=self.family, patient=self.patient)
        self.assertFalse(fp.is_primary)

    def test_unique_family_patient_constraint(self):
        FamilyPatient.objects.create(family=self.family, patient=self.patient)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FamilyPatient.objects.create(family=self.family, patient=self.patient)

    def test_only_one_primary_patient_per_family(self):
        FamilyPatient.objects.create(family=self.family, patient=self.patient, is_primary=True)
        second_patient = make_patient()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                FamilyPatient.objects.create(
                    family=self.family, patient=second_patient, is_primary=True
                )

    def test_multiple_non_primary_patients_allowed(self):
        FamilyPatient.objects.create(family=self.family, patient=self.patient, is_primary=True)
        second_patient = make_patient()
        FamilyPatient.objects.create(family=self.family, patient=second_patient, is_primary=False)
        self.assertEqual(self.family.patients.count(), 2)

    def test_same_patient_can_belong_to_multiple_families(self):
        other_family = Family.objects.create(name="Other Family", created_by=self.owner)
        FamilyPatient.objects.create(family=self.family, patient=self.patient)
        FamilyPatient.objects.create(family=other_family, patient=self.patient)
        self.assertEqual(self.patient.family_relationships.count(), 2)


class FamilyInvitationModelTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner6")
        self.family = Family.objects.create(name="Invite Family", created_by=self.owner)

    def _make_invitation(self, expires_delta, **kwargs):
        defaults = dict(
            family=self.family,
            invited_by=self.owner,
            invitation_type=FamilyInvitation.InvitationType.MEMBER,
            name="Jane Doe",
            email="jane@example.com",
            role=FamilyMember.Role.MEMBER,
            token_hash="a" * 64,
            expires_at=timezone.now() + expires_delta,
        )
        defaults.update(kwargs)
        return FamilyInvitation.objects.create(**defaults)

    def test_str_representation(self):
        invitation = self._make_invitation(timedelta(days=1))
        text = str(invitation)
        self.assertIn(invitation.name, text)
        self.assertIn(str(self.family), text)
        self.assertIn(invitation.invitation_type, text)

    def test_default_status_is_pending(self):
        invitation = self._make_invitation(timedelta(days=1))
        self.assertEqual(invitation.status, FamilyInvitation.Status.PENDING)

    def test_is_expired_false_for_future_expiry(self):
        invitation = self._make_invitation(timedelta(days=1))
        self.assertFalse(invitation.is_expired)

    def test_is_expired_true_for_past_expiry(self):
        invitation = self._make_invitation(timedelta(days=-1))
        self.assertTrue(invitation.is_expired)

    def test_token_hash_must_be_unique(self):
        self._make_invitation(timedelta(days=1), token_hash="b" * 64)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._make_invitation(
                    timedelta(days=1), token_hash="b" * 64, email="other@example.com"
                )

    def test_patient_claim_invitation_links_patient(self):
        patient = make_patient()
        invitation = self._make_invitation(
            timedelta(days=1),
            invitation_type=FamilyInvitation.InvitationType.PATIENT_CLAIM,
            patient=patient,
            token_hash="c" * 64,
            role="",
        )
        self.assertEqual(invitation.patient, patient)

    def test_otp_defaults(self):
        invitation = self._make_invitation(timedelta(days=1), token_hash="d" * 64)
        self.assertEqual(invitation.otp_hash, "")
        self.assertIsNone(invitation.otp_expires_at)
        self.assertEqual(invitation.otp_attempts, 0)
        self.assertIsNone(invitation.contact_verified_at)


class InvitationDeliveryModelTests(TestCase):
    def setUp(self):
        self.owner = make_user("owner7")
        self.family = Family.objects.create(name="Delivery Family", created_by=self.owner)
        self.invitation = FamilyInvitation.objects.create(
            family=self.family,
            invited_by=self.owner,
            invitation_type=FamilyInvitation.InvitationType.MEMBER,
            name="Delivery Target",
            email="target@example.com",
            role=FamilyMember.Role.MEMBER,
            token_hash="e" * 64,
            expires_at=timezone.now() + timedelta(days=1),
        )

    def test_default_status_is_pending(self):
        delivery = InvitationDelivery.objects.create(
            invitation=self.invitation,
            channel=InvitationDelivery.Channel.EMAIL,
            destination="target@example.com",
        )
        self.assertEqual(delivery.status, InvitationDelivery.Status.PENDING)

    def test_delivery_cascades_when_invitation_deleted(self):
        InvitationDelivery.objects.create(
            invitation=self.invitation,
            channel=InvitationDelivery.Channel.SMS,
            destination="+15551234567",
        )
        self.invitation.delete()
        self.assertEqual(InvitationDelivery.objects.count(), 0)

    def test_multiple_deliveries_per_invitation(self):
        InvitationDelivery.objects.create(
            invitation=self.invitation,
            channel=InvitationDelivery.Channel.EMAIL,
            destination="target@example.com",
        )
        InvitationDelivery.objects.create(
            invitation=self.invitation,
            channel=InvitationDelivery.Channel.SMS,
            destination="+15551234567",
        )
        self.assertEqual(self.invitation.deliveries.count(), 2)
