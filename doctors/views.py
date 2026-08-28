from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Specialty,
    Doctor,
    Qualification,
    DoctorAvailability,
)

from .serializers import (
    SpecialtySerializer,
    DoctorListSerializer,
    DoctorDetailSerializer,
    DoctorCreateSerializer,
    DoctorUpdateSerializer,
    QualificationSerializer,
    DoctorAvailabilitySerializer,
)

from .permissions import (
    IsStaffUser,
    IsDoctor,
    IsDoctorOwner,
    IsApprovedDoctorOwner,
)


# ============================================================
# QUERYSETS
# ============================================================

def doctor_queryset():
    """
    Centralized Doctor queryset.

    Prevents unnecessary database queries when accessing
    related user, specialty, qualifications and availability.
    """
    return (
        Doctor.objects
        .select_related(
            "user",
            "specialty",
            "approved_by",
        )
        .prefetch_related(
            "qualifications",
            "availability",
        )
    )


# ============================================================
# SPECIALTY
# ============================================================

class SpecialtyListCreateView(APIView):
    """
    GET:
        List specialties.

    POST:
        Create a specialty.
        Staff only.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = Specialty.objects.all()

        search = request.query_params.get("search")

        if search:
            search = search.strip()

            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search)
                    | Q(description__icontains=search)
                )

        serializer = SpecialtySerializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def post(self, request):

        permission = IsStaffUser()

        if not permission.has_permission(
            request,
            self,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SpecialtySerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        specialty = serializer.save()

        return Response(
            SpecialtySerializer(specialty).data,
            status=status.HTTP_201_CREATED,
        )


class SpecialtyDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):

        return get_object_or_404(
            Specialty,
            pk=pk,
        )

    def get(self, request, pk):

        specialty = self.get_object(pk)

        serializer = SpecialtySerializer(
            specialty,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    def patch(self, request, pk):

        permission = IsStaffUser()

        if not permission.has_permission(
            request,
            self,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        specialty = self.get_object(pk)

        serializer = SpecialtySerializer(
            specialty,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        specialty = serializer.save()

        return Response(
            SpecialtySerializer(
                specialty,
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):

        permission = IsStaffUser()

        if not permission.has_permission(
            request,
            self,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        specialty = self.get_object(pk)

        # Do not physically delete specialties.
        #
        # This assumes Specialty has:
        #     is_active
        #     updated_at

        specialty.is_active = False

        specialty.save(
            update_fields=[
                "is_active",
                "updated_at",
            ],
        )

        return Response(
            {
                "detail": (
                    "Specialty deactivated successfully."
                ),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# DOCTOR LIST / CREATE
# ============================================================

class DoctorListCreateView(APIView):
    """
    GET:
        Authenticated users can browse doctors.

    POST:
        An authenticated user can create their own doctor
        application.

        New doctor applications ALWAYS start as PENDING.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        queryset = doctor_queryset()

        specialty = request.query_params.get(
            "specialty"
        )

        approval_status = request.query_params.get(
            "approval_status"
        )

        verified = request.query_params.get(
            "verified"
        )

        search = request.query_params.get(
            "search"
        )

        # ----------------------------------------------------
        # Specialty filter
        # ----------------------------------------------------

        if specialty:
            queryset = queryset.filter(
                specialty_id=specialty,
            )

        # ----------------------------------------------------
        # Approval status
        # ----------------------------------------------------

        if approval_status:
            allowed_statuses = {
                Doctor.ApprovalStatus.PENDING,
                Doctor.ApprovalStatus.APPROVED,
                Doctor.ApprovalStatus.REJECTED,
                Doctor.ApprovalStatus.SUSPENDED,
            }

            if approval_status not in allowed_statuses:

                return Response(
                    {
                        "detail": (
                            "Invalid approval_status."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Non-staff users should not be able to
            # enumerate pending/rejected doctors.
            if (
                approval_status
                != Doctor.ApprovalStatus.APPROVED
                and not request.user.is_staff
            ):
                return Response(
                    {
                        "detail": (
                            "You do not have permission "
                            "to view this doctor status."
                        ),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            queryset = queryset.filter(
                approval_status=approval_status,
            )

        else:
            # Normal users only see approved doctors.
            if not request.user.is_staff:
                queryset = queryset.filter(
                    approval_status=(
                        Doctor.ApprovalStatus.APPROVED
                    ),
                    user__is_active=True,
                )

        # ----------------------------------------------------
        # Backwards-compatible verified filter
        # ----------------------------------------------------

        if verified is not None:

            if verified.lower() not in {
                "true",
                "false",
            }:
                return Response(
                    {
                        "detail": (
                            "verified must be true or false."
                        ),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Only staff should use the legacy verification
            # filter if this field still exists.
            if not request.user.is_staff:

                return Response(
                    {
                        "detail": (
                            "Only administrators can "
                            "use the verified filter."
                        ),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            queryset = queryset.filter(
                verified=verified.lower() == "true",
            )

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        if search:

            search = search.strip()

            if search:

                queryset = queryset.filter(
                    Q(
                        user__first_name__icontains=search
                    )
                    | Q(
                        user__last_name__icontains=search
                    )
                    | Q(
                        user__username__icontains=search
                    )
                    | Q(
                        specialty__name__icontains=search
                    )
                )

        serializer = DoctorListSerializer(
            queryset,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def post(self, request):

        # ----------------------------------------------------
        # Account must be active
        # ----------------------------------------------------

        if not request.user.is_active:

            return Response(
                {
                    "detail": (
                        "Inactive users cannot "
                        "create doctor applications."
                    ),
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # ----------------------------------------------------
        # One Doctor profile per User
        # ----------------------------------------------------

        if Doctor.objects.filter(
            user=request.user,
        ).exists():

            return Response(
                {
                    "detail": (
                        "This user already has "
                        "a doctor profile."
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        serializer = DoctorCreateSerializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        doctor = serializer.save()

        # Make absolutely sure the application starts
        # in pending state.
        if doctor.approval_status != (
            Doctor.ApprovalStatus.PENDING
        ):
            doctor.approval_status = (
                Doctor.ApprovalStatus.PENDING
            )

            doctor.save(
                update_fields=[
                    "approval_status",
                ],
            )

        return Response(
            DoctorDetailSerializer(
                doctor,
            ).data,
            status=status.HTTP_201_CREATED,
        )


# ============================================================
# DOCTOR DETAIL
# ============================================================

class DoctorDetailView(APIView):
    """
    GET:
        Retrieve doctor.

    PATCH:
        Doctor owner or staff.

    DELETE:
        Intentionally not supported.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):

        return get_object_or_404(
            doctor_queryset(),
            pk=pk,
        )

    def get(self, request, pk):

        doctor = self.get_object(pk)

        # ----------------------------------------------------
        # Non-staff users may only retrieve approved doctors
        # ----------------------------------------------------

        if not request.user.is_staff:

            if (
                doctor.approval_status
                != Doctor.ApprovalStatus.APPROVED
            ):
                return Response(
                    {
                        "detail": (
                            "This doctor profile "
                            "is not publicly available."
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            if not doctor.user.is_active:

                return Response(
                    {
                        "detail": (
                            "This doctor profile "
                            "is not currently available."
                        ),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        serializer = DoctorDetailSerializer(
            doctor,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(self, request, pk):

        doctor = self.get_object(pk)

        # ----------------------------------------------------
        # Staff can modify any doctor.
        # Doctor can modify only their own profile.
        # ----------------------------------------------------

        if request.user.is_staff:

            permission = IsStaffUser()

            if not permission.has_permission(
                request,
                self,
            ):
                return Response(
                    {
                        "detail": permission.message,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        else:

            permission = IsDoctorOwner()

            if not permission.has_object_permission(
                request,
                self,
                doctor,
            ):
                return Response(
                    {
                        "detail": permission.message,
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        # ----------------------------------------------------
        # Never allow self-service modification of approval
        # ----------------------------------------------------

        protected_fields = {
            "id",
            "user",
            "approval_status",
            "verified",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        }

        attempted = (
            protected_fields
            & set(request.data.keys())
        )

        if attempted:

            return Response(
                {
                    "detail": (
                        "The following fields cannot "
                        "be modified through this endpoint: "
                        f"{sorted(attempted)}"
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DoctorUpdateSerializer(
            doctor,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        doctor = serializer.save()

        return Response(
            DoctorDetailSerializer(
                doctor,
            ).data,
            status=status.HTTP_200_OK,
        )

    def delete(self, request, pk):

        return Response(
            {
                "detail": (
                    "Doctor profiles cannot be deleted. "
                    "Use account deactivation instead."
                ),
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )


# ============================================================
# CURRENT DOCTOR
# ============================================================

class DoctorMeView(APIView):
    """
    GET:
        Current user's doctor profile.

    PATCH:
        Update own doctor profile.

    This endpoint is useful for the frontend because it
    doesn't require storing the Doctor ID separately.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):

        doctor = get_object_or_404(
            doctor_queryset(),
            user=request.user,
        )

        serializer = DoctorDetailSerializer(
            doctor,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(self, request):

        doctor = get_object_or_404(
            doctor_queryset(),
            user=request.user,
        )

        permission = IsDoctorOwner()

        if not permission.has_object_permission(
            request,
            self,
            doctor,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        protected_fields = {
            "id",
            "user",
            "approval_status",
            "verified",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "created_at",
            "updated_at",
        }

        attempted = (
            protected_fields
            & set(request.data.keys())
        )

        if attempted:

            return Response(
                {
                    "detail": (
                        "Protected fields cannot "
                        "be modified."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = DoctorUpdateSerializer(
            doctor,
            data=request.data,
            partial=True,
            context={
                "request": request,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        doctor = serializer.save()

        return Response(
            DoctorDetailSerializer(
                doctor,
            ).data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# DOCTOR ACCOUNT DEACTIVATION
# ============================================================

class DoctorDeactivateAccountView(APIView):
    """
    Doctor deactivates their own User account.

    The Doctor record is preserved.
    """

    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):

        doctor = get_object_or_404(
            Doctor,
            user=request.user,
        )

        permission = IsDoctorOwner()

        if not permission.has_object_permission(
            request,
            self,
            doctor,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not request.user.is_active:

            return Response(
                {
                    "detail": (
                        "Your account is already inactive."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.is_active = False

        request.user.save(
            update_fields=[
                "is_active",
            ],
        )

        return Response(
            {
                "detail": (
                    "Your account has been "
                    "deactivated successfully."
                ),
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# ADMIN: APPROVE DOCTOR
# ============================================================

class DoctorApproveView(APIView):
    """
    Only staff users can approve a doctor.
    """

    permission_classes = [IsStaffUser]

    @transaction.atomic
    def post(self, request, pk):

        doctor = get_object_or_404(
            Doctor.objects.select_related("user"),
            pk=pk,
        )

        if doctor.approval_status == (
            Doctor.ApprovalStatus.APPROVED
        ):
            return Response(
                {
                    "detail": (
                        "Doctor is already approved."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctor.approval_status = (
            Doctor.ApprovalStatus.APPROVED
        )

        doctor.approved_by = request.user
        doctor.approved_at = timezone.now()
        doctor.rejection_reason = ""

        doctor.save(
            update_fields=[
                "approval_status",
                "approved_by",
                "approved_at",
                "rejection_reason",
                "updated_at",
            ],
        )

        return Response(
            DoctorDetailSerializer(
                doctor,
            ).data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# ADMIN: REJECT DOCTOR
# ============================================================

class DoctorRejectView(APIView):
    """
    Only staff users can reject a doctor application.

    A rejection reason is mandatory.
    """

    permission_classes = [IsStaffUser]

    @transaction.atomic
    def post(self, request, pk):

        doctor = get_object_or_404(
            Doctor,
            pk=pk,
        )

        reason = request.data.get(
            "reason",
        )

        if not reason or not str(reason).strip():

            return Response(
                {
                    "detail": (
                        "A rejection reason is required."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if doctor.approval_status == (
            Doctor.ApprovalStatus.SUSPENDED
        ):

            return Response(
                {
                    "detail": (
                        "A suspended doctor cannot "
                        "be rejected."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        doctor.approval_status = (
            Doctor.ApprovalStatus.REJECTED
        )

        doctor.rejection_reason = str(
            reason
        ).strip()

        doctor.approved_by = None
        doctor.approved_at = None

        doctor.save(
            update_fields=[
                "approval_status",
                "rejection_reason",
                "approved_by",
                "approved_at",
                "updated_at",
            ],
        )

        return Response(
            DoctorDetailSerializer(
                doctor,
            ).data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# ADMIN: SUSPEND DOCTOR
# ============================================================

class DoctorSuspendView(APIView):
    """
    Only staff users can suspend an approved doctor.
    """

    permission_classes = [IsStaffUser]

    @transaction.atomic
    def post(self, request, pk):

        doctor = get_object_or_404(
            Doctor,
            pk=pk,
        )

        if doctor.approval_status != (
            Doctor.ApprovalStatus.APPROVED
        ):

            return Response(
                {
                    "detail": (
                        "Only approved doctors "
                        "can be suspended."
                    ),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        reason = request.data.get(
            "reason",
            "",
        )

        doctor.approval_status = (
            Doctor.ApprovalStatus.SUSPENDED
        )

        doctor.rejection_reason = str(
            reason
        ).strip()

        doctor.save(
            update_fields=[
                "approval_status",
                "rejection_reason",
                "updated_at",
            ],
        )

        return Response(
            DoctorDetailSerializer(
                doctor,
            ).data,
            status=status.HTTP_200_OK,
        )


# ============================================================
# QUALIFICATIONS
# ============================================================

class QualificationListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get_doctor(self, doctor_id):

        return get_object_or_404(
            Doctor,
            pk=doctor_id,
        )

    def get(self, request, doctor_id):

        doctor = self.get_doctor(
            doctor_id,
        )

        qualifications = (
            Qualification.objects
            .filter(
                doctor=doctor,
            )
            .order_by(
                "-year_of_completion",
            )
        )

        serializer = QualificationSerializer(
            qualifications,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def post(self, request, doctor_id):

        doctor = self.get_doctor(
            doctor_id,
        )

        permission = IsApprovedDoctorOwner()

        if not permission.has_object_permission(
            request,
            self,
            doctor,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = QualificationSerializer(
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        qualification = serializer.save(
            doctor=doctor,
        )

        return Response(
            QualificationSerializer(
                qualification,
            ).data,
            status=status.HTTP_201_CREATED,
        )


class QualificationDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(
        self,
        doctor_id,
        pk,
    ):

        return get_object_or_404(
            Qualification.objects.select_related(
                "doctor__user",
            ),
            pk=pk,
            doctor_id=doctor_id,
        )

    def get(
        self,
        request,
        doctor_id,
        pk,
    ):

        qualification = self.get_object(
            doctor_id,
            pk,
        )

        serializer = QualificationSerializer(
            qualification,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(
        self,
        request,
        doctor_id,
        pk,
    ):

        qualification = self.get_object(
            doctor_id,
            pk,
        )

        permission = IsApprovedDoctorOwner()

        if not permission.has_object_permission(
            request,
            self,
            qualification.doctor,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = QualificationSerializer(
            qualification,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True,
        )

        qualification = serializer.save()

        return Response(
            QualificationSerializer(
                qualification,
            ).data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def delete(
        self,
        request,
        doctor_id,
        pk,
    ):

        qualification = self.get_object(
            doctor_id,
            pk,
        )

        permission = IsApprovedDoctorOwner()

        if not permission.has_object_permission(
            request,
            self,
            qualification.doctor,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        qualification.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


# ============================================================
# AVAILABILITY
# ============================================================

class DoctorAvailabilityListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get_doctor(self, doctor_id):

        return get_object_or_404(
            Doctor,
            pk=doctor_id,
        )

    def get(self, request, doctor_id):

        doctor = self.get_doctor(
            doctor_id,
        )

        availability = (
            DoctorAvailability.objects
            .filter(
                doctor=doctor,
            )
            .order_by(
                "day",
                "start_time",
            )
        )

        serializer = DoctorAvailabilitySerializer(
            availability,
            many=True,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def post(self, request, doctor_id):

        doctor = self.get_doctor(
            doctor_id,
        )

        permission = IsApprovedDoctorOwner()

        if not permission.has_object_permission(
            request,
            self,
            doctor,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DoctorAvailabilitySerializer(
            data=request.data,
            context={
                "request": request,
                "doctor": doctor,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        availability = serializer.save(
            doctor=doctor,
        )

        return Response(
            DoctorAvailabilitySerializer(
                availability,
            ).data,
            status=status.HTTP_201_CREATED,
        )


class DoctorAvailabilityDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get_object(
        self,
        doctor_id,
        pk,
    ):

        return get_object_or_404(
            DoctorAvailability.objects.select_related(
                "doctor__user",
            ),
            pk=pk,
            doctor_id=doctor_id,
        )

    def get(
        self,
        request,
        doctor_id,
        pk,
    ):

        availability = self.get_object(
            doctor_id,
            pk,
        )

        serializer = DoctorAvailabilitySerializer(
            availability,
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def patch(
        self,
        request,
        doctor_id,
        pk,
    ):

        availability = self.get_object(
            doctor_id,
            pk,
        )

        permission = IsApprovedDoctorOwner()

        if not permission.has_object_permission(
            request,
            self,
            availability.doctor,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = DoctorAvailabilitySerializer(
            availability,
            data=request.data,
            partial=True,
            context={
                "request": request,
                "doctor": availability.doctor,
            },
        )

        serializer.is_valid(
            raise_exception=True,
        )

        availability = serializer.save()

        return Response(
            DoctorAvailabilitySerializer(
                availability,
            ).data,
            status=status.HTTP_200_OK,
        )

    @transaction.atomic
    def delete(
        self,
        request,
        doctor_id,
        pk,
    ):

        availability = self.get_object(
            doctor_id,
            pk,
        )

        permission = IsApprovedDoctorOwner()

        if not permission.has_object_permission(
            request,
            self,
            availability.doctor,
        ):
            return Response(
                {
                    "detail": permission.message,
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        availability.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )