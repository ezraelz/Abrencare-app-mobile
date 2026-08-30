from django.contrib import admin

from .models import Consultation, Prescription


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 0

    fields = (
        "medication",
        "dosage",
        "frequency",
        "duration",
        "instructions",
        "created_at",
        "updated_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "patient_name",
        "doctor_name",
        "consultation_type",
        "language",
        "status",
        "price",
        "currency",
        "appointment_date",
        "appointment_time",
        "started_at",
        "ended_at",
        "created_at",
    )

    list_filter = (
        "status",
        "consultation_type",
        "language",
        "currency",
        "created_at",
    )

    search_fields = (
        "appointment__patient__user__full_name",
        "appointment__doctor__user__full_name",
        "appointment__patient__user__email",
        "appointment__doctor__user__email",
        "meeting_url",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "appointment",
        "appointment__patient",
        "appointment__patient__user",
        "appointment__doctor",
        "appointment__doctor__user",
    )

    fieldsets = (
        (
            "Appointment",
            {
                "fields": (
                    "appointment",
                )
            },
        ),
        (
            "Consultation Details",
            {
                "fields": (
                    "consultation_type",
                    "language",
                    "status",
                )
            },
        ),
        (
            "Payment",
            {
                "fields": (
                    "price",
                    "currency",
                )
            },
        ),
        (
            "Meeting",
            {
                "fields": (
                    "meeting_url",
                    "started_at",
                    "ended_at",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    inlines = (
        PrescriptionInline,
    )

    @admin.display(description="Patient", ordering="appointment__patient__user__full_name")
    def patient_name(self, obj):
        return obj.appointment.patient.user.full_name

    @admin.display(description="Doctor", ordering="appointment__doctor__user__full_name")
    def doctor_name(self, obj):
        return obj.appointment.doctor.user.full_name

    @admin.display(
        description="Appointment Date",
        ordering="appointment__appointment_date",
    )
    def appointment_date(self, obj):
        return obj.appointment.appointment_date

    @admin.display(
        description="Appointment Time",
        ordering="appointment__appointment_time",
    )
    def appointment_time(self, obj):
        return obj.appointment.appointment_time


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "consultation",
        "medication",
        "dosage",
        "frequency",
        "duration",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "medication",
        "dosage",
        "frequency",
        "instructions",
        "consultation__appointment__patient__user__full_name",
        "consultation__appointment__doctor__user__full_name",
    )

    date_hierarchy = "created_at"

    ordering = (
        "-created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    list_select_related = (
        "consultation",
        "consultation__appointment",
        "consultation__appointment__patient",
        "consultation__appointment__patient__user",
        "consultation__appointment__doctor",
        "consultation__appointment__doctor__user",
    )

    fieldsets = (
        (
            "Consultation",
            {
                "fields": (
                    "consultation",
                )
            },
        ),
        (
            "Medication",
            {
                "fields": (
                    "medication",
                    "dosage",
                    "frequency",
                    "duration",
                    "instructions",
                )
            },
        ),
        (
            "System Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )