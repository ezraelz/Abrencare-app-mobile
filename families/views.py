from django.shortcuts import get_object_or_404

from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Family,
    FamilyMember,
    FamilyPatient,
    FamilyInvitation,
    InvitationDelivery,
    FamilyAuditLog
)

from .permissions import (
    IsFamilyMember,
    CanManageFamilyMembers,
    CanManageFamilyPatients,
)

from .serializers import (
    FamilySerializer,
    FamilyMemberSerializer,
    FamilyPatientSerializer,
    FamilyPatientDetailSerializer,
    FamilyInvitationSerializer,
    InvitationDeliverySerializer,
    CreateFamilyMemberInvitationSerializer,
    CreateFamilyPatientSerializer,
    CreatePatientClaimInvitationSerializer,
    AcceptInvitationSerializer,
    VerifyInvitationOTPSerializer,
    CompleteInvitationRegistrationSerializer,
    FamilyAuditLogSerializer
)

from .services import (
    create_family,
    create_family_patient,
    invite_family_member,
    create_patient_claim_invitation,
    get_invitation_by_token,
    request_invitation_contact_verification,
    verify_invitation_otp,
    accept_invitation,
    complete_invitation_registration,
    complete_patient_claim,
)


# ============================================================
# HELPERS
# ============================================================

def get_family_or_404(family_id):
    """
    Return a family or raise HTTP 404.
    """
    return get_object_or_404(
        Family,
        id=family_id,
    )


def get_pending_invitation(token):
    """
    Resolve an invitation through the service layer.

    Token hashing, expiration handling and status validation
    belong to the service layer rather than the view.
    """
    return get_invitation_by_token(token)


# ============================================================
# FAMILY
# ============================================================

class FamilyListCreateView(APIView):
    """
    GET: Return families where the authenticated user is a member.
    POST: Create a new family and automatically make the creator its owner.
    """
    permission_classes = [IsAuthenticated,]

    def get(self, request):
        families = (Family.objects.filter(members__user=request.user,).distinct()
            .prefetch_related(
                "members",
                "patients",
            )
        )

        serializer = FamilySerializer(
            families,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        serializer = FamilySerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        family = create_family(
            user=request.user,
            name=serializer.validated_data["name"],
        )

        return Response(
            FamilySerializer(family).data,
            status=status.HTTP_201_CREATED,
        )


class FamilyDetailView(APIView):
    """
    Retrieve or update a family.
    Only an existing family member can access the family.
    """

    permission_classes = [
        IsAuthenticated,
        IsFamilyMember,
    ]

    def get_object(self, family_id):
        return get_family_or_404(family_id)

    def get(self, request, family_id):
        family = self.get_object(family_id)

        return Response(
            FamilySerializer(family).data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, family_id):
        family = self.get_object(family_id)

        serializer = FamilySerializer(
            family,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        serializer.save()

        return Response(
            FamilySerializer(family).data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# FAMILY MEMBERS
# ============================================================

class FamilyMemberListView(APIView):
    """
    List all members of a family.
    Membership authorization is handled by IsFamilyMember.
    """

    permission_classes = [
        IsAuthenticated,
        IsFamilyMember,
    ]

    def get(self, request, family_id):

        family = get_family_or_404(
            family_id,
        )

        members = (
            FamilyMember.objects
            .filter(
                family=family,
            )
            .select_related(
                "user",
                "family",
            )
            .order_by(
                "created_at",
            )
        )

        serializer = FamilyMemberSerializer(
            members,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# FAMILY PATIENTS
# ============================================================

class FamilyPatientListView(APIView):
    """
    List patients associated with a family.
    """

    permission_classes = [
        IsAuthenticated,
        IsFamilyMember,
    ]

    def get(self, request, family_id):

        family = get_family_or_404(
            family_id,
        )

        patients = (
            FamilyPatient.objects
            .filter(
                family=family,
            )
            .select_related(
                "family",
                "patient",
                "patient__user",
            )
            .order_by(
                "created_at",
            )
        )

        serializer = FamilyPatientSerializer(
            patients,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class FamilyPatientDetailView(APIView):
    """
    Retrieve detailed information about a patient belonging
    to a family.

    Medical records are intentionally not exposed here.
    """

    permission_classes = [
        IsAuthenticated,
        IsFamilyMember,
    ]

    def get(
        self,
        request,
        family_id,
        patient_id,
    ):

        family = get_family_or_404(
            family_id,
        )

        family_patient = get_object_or_404(
            FamilyPatient.objects.select_related(
                "patient",
                "patient__user",
            ),
            family=family,
            patient_id=patient_id,
        )

        serializer = FamilyPatientDetailSerializer(
            family_patient.patient,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# CREATE FAMILY PATIENT
# ============================================================

class FamilyPatientCreateView(APIView):
    """
    Create a patient and associate the patient with a family.

    The service handles:
        User reuse/creation
        Patient creation
        FamilyPatient creation
        duplicate prevention
    """

    permission_classes = [
        IsAuthenticated,
        CanManageFamilyPatients,
    ]

    def post(self, request, family_id):

        family = get_family_or_404(
            family_id,
        )

        serializer = CreateFamilyPatientSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            family_patient = create_family_patient(
                family=family,
                created_by=request.user,
                validated_data=serializer.validated_data,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            FamilyPatientSerializer(
                family_patient,
            ).data,
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# INVITE FAMILY MEMBER
# ============================================================

class FamilyMemberInvitationCreateView(APIView):
    """
    Create an invitation for a new family member.

    The raw token is intentionally never returned to the client.
    """

    permission_classes = [
        IsAuthenticated,
        CanManageFamilyMembers,
    ]

    def post(self, request, family_id):

        family = get_family_or_404(
            family_id,
        )

        serializer = CreateFamilyMemberInvitationSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            invitation, raw_token = invite_family_member(
                family=family,
                invited_by=request.user,
                validated_data=serializer.validated_data,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # IMPORTANT:
        #
        # raw_token exists only in this request lifecycle.
        #
        # Pass it to the notification service here.
        #
        # queue_family_invitation_notification.delay(
        #     invitation.id,
        #     raw_token,
        # )

        return Response(
            FamilyInvitationSerializer(
                invitation,
            ).data,
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# PATIENT CLAIM INVITATION
# ============================================================

class PatientClaimInvitationCreateView(APIView):
    """
    Create an invitation allowing a pending patient to
    claim their existing account.
    """

    permission_classes = [
        IsAuthenticated,
        CanManageFamilyPatients,
    ]

    def post(
        self,
        request,
        family_id,
        patient_id,
    ):

        family = get_family_or_404(
            family_id,
        )

        family_patient = get_object_or_404(
            FamilyPatient.objects.select_related(
                "patient",
                "patient__user",
            ),
            family=family,
            patient_id=patient_id,
        )

        serializer = CreatePatientClaimInvitationSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            invitation, raw_token = (
                create_patient_claim_invitation(
                    family=family,
                    patient=family_patient.patient,
                    invited_by=request.user,
                    validated_data=serializer.validated_data,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Send through notification layer.
        #
        # queue_patient_claim_notification.delay(
        #     invitation.id,
        #     raw_token,
        # )

        return Response(
            FamilyInvitationSerializer(
                invitation,
            ).data,
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# INVITATION DETAILS
# ============================================================

class InvitationDetailView(APIView):
    """
    Public invitation lookup.

    No authentication is required because the recipient may
    not have an account yet.

    The service layer is responsible for:
        token hashing
        expiration
        status validation
    """

    permission_classes = [
        AllowAny,
    ]

    def get(self, request, token):

        try:
            invitation = get_pending_invitation(
                token,
            )

        except ValueError as exc:
            return Response(
                {
                    "valid": False,
                    "detail": str(exc),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "valid": True,
                "invitation": FamilyInvitationSerializer(
                    invitation,
                ).data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# REQUEST CONTACT VERIFICATION
# ============================================================

class InvitationContactVerificationView(APIView):
    """
    Start contact verification for an invitation.

    This endpoint does NOT accept the invitation.

    It only triggers the OTP delivery process.
    """

    permission_classes = [
        AllowAny,
    ]

    def post(self, request, token):

        try:
            result = request_invitation_contact_verification(
                token=token,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


# ============================================================
# VERIFY INVITATION OTP
# ============================================================

class InvitationOTPVerificationView(APIView):

    permission_classes = [
        AllowAny,
    ]

    def post(self, request, token):

        serializer = VerifyInvitationOTPSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            result = verify_invitation_otp(
                token=token,
                otp=serializer.validated_data["otp"],
            )

        except ValueError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_200_OK,
        )


# ============================================================
# ACCEPT INVITATION — EXISTING USER
# ============================================================

class InvitationAcceptView(APIView):
    """
    Accept a family-member invitation for an existing
    authenticated user.

    Required security layers:

        authenticated user
        +
        invitation token
        +
        verified contact
    """

    permission_classes = [
        IsAuthenticated,
    ]

    def post(self, request, token):

        serializer = AcceptInvitationSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            member = accept_invitation(
                token=token,
                user=request.user,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            FamilyMemberSerializer(
                member,
            ).data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# COMPLETE INVITATION REGISTRATION
# ============================================================

class InvitationRegistrationView(APIView):
    """
    Complete registration for an invited person who does
    not already have an active account.

    The invitation/contact verification must already have
    succeeded.
    """

    permission_classes = [
        AllowAny,
    ]

    def post(self, request, token):

        serializer = (
            CompleteInvitationRegistrationSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            user, member = (
                complete_invitation_registration(
                    token=token,
                    validated_data=serializer.validated_data,
                )
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "account_status": user.account_status,
                },
                "family_member": (
                    FamilyMemberSerializer(
                        member,
                    ).data
                ),
            },
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# COMPLETE PATIENT CLAIM
# ============================================================

class PatientClaimCompletionView(APIView):
    """
    Complete a patient account claim.

    The existing Patient object is retained.

    The service must:
        verify invitation
        verify contact
        activate/create the User
        set password
        retain existing Patient
        accept invitation
    """

    permission_classes = [
        AllowAny,
    ]

    def post(self, request, token):

        serializer = (
            CompleteInvitationRegistrationSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True,
        )

        try:
            user, patient = complete_patient_claim(
                token=token,
                validated_data=serializer.validated_data,
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "account_status": user.account_status,
                },
                "patient": {
                    "id": patient.id,
                },
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# INVITATION DELIVERY HISTORY
# ============================================================

class InvitationDeliveryListView(APIView):
    """
    List delivery attempts for an invitation.

    This is intentionally restricted to authenticated users
    with access to the relevant family.
    """

    permission_classes = [
        IsAuthenticated,
        IsFamilyMember,
    ]

    def get(self, request, family_id, invitation_id):

        family = get_family_or_404(
            family_id,
        )

        invitation = get_object_or_404(
            FamilyInvitation,
            id=invitation_id,
            family=family,
        )

        deliveries = (
            InvitationDelivery.objects
            .filter(
                invitation=invitation,
            )
            .order_by(
                "-created_at",
            )
        )

        serializer = InvitationDeliverySerializer(
            deliveries,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )


class FamilyAuditLogListView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsFamilyMember,
    ]

    def get(self, request, family_id):
        family = get_object_or_404(
            Family,
            id=family_id,
        )

        if not FamilyMember.objects.filter(
            family=family,
            user=request.user,
        ).exists():
            raise PermissionDenied(
                "You are not a member of this family."
            )

        logs = (
            FamilyAuditLog.objects
            .filter(family=family)
            .select_related(
                "actor",
                "invitation",
                "patient",
            )
            .order_by("-created_at")
        )

        serializer = FamilyAuditLogSerializer(
            logs,
            many=True,
        )

        return Response(
            serializer.data
        )
     