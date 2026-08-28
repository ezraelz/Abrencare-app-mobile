from django.contrib import admin

from .models import (
    Doctor,
    Specialty,
    Qualification,
    DoctorAvailability,
)


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "is_active",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "is_active",
    )

    search_fields = (
        "name",
        "description",
    )

    ordering = (
        "name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    list_display = (
        "get_full_name",
        "get_email",
        "specialty",
        "license_number",
        "years_of_experience",
        "consultation_fee",
        "created_at",
    )

    list_filter = (
        "specialty",
    )

    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
        "license_number",
    )

    autocomplete_fields = (
        "user",
        "specialty",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "user__first_name",
        "user__last_name",
    )

    @admin.display(
        description="Doctor"
    )
    def get_full_name(self, obj):
        return (
            obj.user.full_name
            or obj.user.username
        )

    @admin.display(
        description="Email"
    )
    def get_email(self, obj):
        return obj.user.email


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):

    list_display = (
        "doctor",
        "degree",
        "institution",
        "year_of_completion",
        "created_at",
    )

    list_filter = (
        "year_of_completion",
    )

    search_fields = (
        "doctor__user__first_name",
        "doctor__user__last_name",
        "doctor__user__username",
        "degree",
        "institution",
    )

    autocomplete_fields = (
        "doctor",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "-year_of_completion",
    )


@admin.register(DoctorAvailability)
class DoctorAvailabilityAdmin(admin.ModelAdmin):

    list_display = (
        "doctor",
        "day",
        "start_time",
        "end_time",
        "is_available",
        "created_at",
    )

    list_filter = (
        "day",
        "is_available",
    )

    search_fields = (
        "doctor__user__first_name",
        "doctor__user__last_name",
        "doctor__user__username",
    )

    autocomplete_fields = (
        "doctor",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    ordering = (
        "doctor",
        "day",
        "start_time",
    )