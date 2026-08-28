from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "patient_name",
        "doctor_name",
        "appointment_date",
        "appointment_time",
        "duration_minutes",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "appointment_date",
        "doctor",
    )

    search_fields = (
        "patient__user__first_name",
        "patient__user__last_name",
        "patient__user__email",
        "doctor__user__first_name",
        "doctor__user__last_name",
        "doctor__user__email",
        "reason_for_visit",
    )

    autocomplete_fields = (
        "patient",
        "doctor",
        "cancelled_by",
    )

    readonly_fields = (
        "duration_minutes",
        "confirmed_at",
        "completed_at",
        "cancelled_at",
        "created_at",
        "updated_at",
    )

    date_hierarchy = "appointment_date"

    ordering = (
        "-appointment_date",
        "-appointment_time",
    )

    @admin.display(description="Patient")
    def patient_name(self, obj):
        return obj.patient.user.full_name

    @admin.display(description="Doctor")
    def doctor_name(self, obj):
        return obj.doctor.user.full_name
    