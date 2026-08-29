"""
Permission tests for the families app.

Run with:
    python manage.py test families.tests.test_permissions
"""
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from families.models import Family, FamilyMember
from families.permissions import (
    IsFamilyMember,
    IsFamilyOwner,
    CanManageFamilyMembers,
    CanManageFamilyPatients,
)

User = get_user_model()


def make_user(username, **kwargs):
    defaults = {"email": f"{username}@example.com"}
    defaults.update(kwargs)
    return User.objects.create_user(username=username, password="testpass123", **defaults)


class FakeView:
    def __init__(self, kwargs):
        self.kwargs = kwargs


class BasePermissionTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.owner = make_user("permowner")
        self.member = make_user("permmember")
        self.outsider = make_user("permoutsider")
        self.family = Family.objects.create(name="Perm Family", created_by=self.owner)
        FamilyMember.objects.create(
            family=self.family, user=self.owner, role=FamilyMember.Role.OWNER
        )
        FamilyMember.objects.create(
            family=self.family, user=self.member, role=FamilyMember.Role.MEMBER
        )

    def _request(self, user):
        request = self.factory.get("/")
        request.user = user
        return request


class IsFamilyMemberTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = IsFamilyMember()

    def test_member_has_permission(self):
        view = FakeView({"family_id": self.family.id})
        self.assertTrue(
            self.permission.has_permission(self._request(self.member), view)
        )

    def test_owner_has_permission(self):
        view = FakeView({"family_id": self.family.id})
        self.assertTrue(
            self.permission.has_permission(self._request(self.owner), view)
        )

    def test_outsider_denied(self):
        view = FakeView({"family_id": self.family.id})
        self.assertFalse(
            self.permission.has_permission(self._request(self.outsider), view)
        )

    def test_unauthenticated_denied(self):
        view = FakeView({"family_id": self.family.id})
        request = self.factory.get("/")
        request.user = None
        self.assertFalse(self.permission.has_permission(request, view))

    def test_falls_back_to_pk_kwarg(self):
        view = FakeView({"pk": self.family.id})
        self.assertTrue(
            self.permission.has_permission(self._request(self.member), view)
        )

    def test_missing_family_id_denied(self):
        view = FakeView({})
        self.assertFalse(
            self.permission.has_permission(self._request(self.member), view)
        )


class IsFamilyOwnerTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = IsFamilyOwner()

    def test_owner_has_permission(self):
        view = FakeView({"family_id": self.family.id})
        self.assertTrue(
            self.permission.has_permission(self._request(self.owner), view)
        )

    def test_non_owner_member_denied(self):
        view = FakeView({"family_id": self.family.id})
        self.assertFalse(
            self.permission.has_permission(self._request(self.member), view)
        )

    def test_outsider_denied(self):
        view = FakeView({"family_id": self.family.id})
        self.assertFalse(
            self.permission.has_permission(self._request(self.outsider), view)
        )


class CanManageFamilyMembersTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = CanManageFamilyMembers()

    def test_member_with_flag_allowed(self):
        FamilyMember.objects.filter(family=self.family, user=self.member).update(
            can_manage_family_members=True
        )
        view = FakeView({"family_id": self.family.id})
        self.assertTrue(
            self.permission.has_permission(self._request(self.member), view)
        )

    def test_member_without_flag_denied(self):
        view = FakeView({"family_id": self.family.id})
        self.assertFalse(
            self.permission.has_permission(self._request(self.member), view)
        )

    def test_owner_has_flag_by_default(self):
        # create_family sets can_manage_family_members=True for the owner,
        # but this row was created directly in setUp without the flag —
        # verify the permission still correctly reads whatever is stored.
        FamilyMember.objects.filter(family=self.family, user=self.owner).update(
            can_manage_family_members=True
        )
        view = FakeView({"family_id": self.family.id})
        self.assertTrue(
            self.permission.has_permission(self._request(self.owner), view)
        )


class CanManageFamilyPatientsTests(BasePermissionTestCase):
    def setUp(self):
        super().setUp()
        self.permission = CanManageFamilyPatients()

    def test_member_with_flag_allowed(self):
        FamilyMember.objects.filter(family=self.family, user=self.member).update(
            can_manage_family_patients=True
        )
        view = FakeView({"family_id": self.family.id})
        self.assertTrue(
            self.permission.has_permission(self._request(self.member), view)
        )

    def test_member_without_flag_denied(self):
        view = FakeView({"family_id": self.family.id})
        self.assertFalse(
            self.permission.has_permission(self._request(self.member), view)
        )

    def test_outsider_denied(self):
        view = FakeView({"family_id": self.family.id})
        self.assertFalse(
            self.permission.has_permission(self._request(self.outsider), view)
        )
