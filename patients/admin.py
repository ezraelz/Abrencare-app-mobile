from django.contrib import admin

from .models import (
    Patient,
    EmergencyContact,
    MedicalRecord,
    MedicalDocument,
)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient_name",
        "patient_email",
        "gender",
        "blood_group",
        "account_status",
        "created_at",
    )

    list_filter = (
        "gender",
        "blood_group",
        "user__is_active",
        "created_at",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "user__phone_number",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "user",
    )

    def patient_name(self, obj):
        return obj.user.full_name

    patient_name.short_description = "Patient"

    def patient_email(self, obj):
        return obj.user.email

    patient_email.short_description = "Email"

    def account_status(self, obj):
        return obj.user.status

    account_status.short_description = "Account Status"


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "patient",
        "relationship",
        "phone_number",
        "is_primary",
        "created_at",
    )

    list_filter = (
        "relationship",
        "is_primary",
        "created_at",
    )

    search_fields = (
        "name",
        "phone_number",
        "patient__user__username",
        "patient__user__email",
        "patient__user__first_name",
        "patient__user__last_name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "patient__user",
    )


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "doctor",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "patient__user__username",
        "patient__user__email",
        "patient__user__first_name",
        "patient__user__last_name",
        "doctor__user__username",
        "diagnosis",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "patient__user",
        "doctor__user",
    )


@admin.register(MedicalDocument)
class MedicalDocumentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient",
        "uploaded_by",
        "description",
        "uploaded_at",
    )

    list_filter = (
        "uploaded_at",
    )

    search_fields = (
        "patient__user__username",
        "patient__user__email",
        "patient__user__first_name",
        "patient__user__last_name",
        "description",
        "uploaded_by__username",
    )

    readonly_fields = (
        "uploaded_at",
    )

    list_select_related = (
        "patient__user",
        "uploaded_by",
    )
    