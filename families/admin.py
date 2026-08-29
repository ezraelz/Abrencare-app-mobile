from django.contrib import admin

from .models import (
    Family,
    FamilyMember,
    FamilyPatient,
)


class FamilyMemberInline(
    admin.TabularInline
):
    model = FamilyMember
    extra = 0
    autocomplete_fields = ["user"]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]


class FamilyPatientInline(
    admin.TabularInline
):
    model = FamilyPatient
    extra = 0
    autocomplete_fields = ["patient"]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):

    list_display = [
        "name",
        "created_by",
        "member_count",
        "patient_count",
        "created_at",
    ]

    search_fields = [
        "name",
        "created_by__full_name",
        "created_by__username",
    ]

    list_filter = [
        "created_at",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]

    inlines = [
        FamilyMemberInline,
        FamilyPatientInline,
    ]

    @admin.display(
        description="Members"
    )
    def member_count(self, obj):
        return obj.members.count()

    @admin.display(
        description="Patients"
    )
    def patient_count(self, obj):
        return obj.patients.count()


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):

    list_display = [
        "user",
        "family",
        "role",
        "can_view_patient_records",
        "can_manage_appointments",
        "can_manage_medications",
        "created_at",
    ]

    list_filter = [
        "role",
        "can_view_patient_records",
        "can_manage_appointments",
        "can_manage_medications",
    ]

    search_fields = [
        "user__full_name",
        "user__username",
        "user__email",
        "family__name",
    ]

    autocomplete_fields = [
        "family",
        "user",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]


@admin.register(FamilyPatient)
class FamilyPatientAdmin(admin.ModelAdmin):

    list_display = [
        "patient",
        "family",
        "relationship",
        "is_primary",
        "created_at",
    ]

    list_filter = [
        "relationship",
        "is_primary",
    ]

    search_fields = [
        "patient__user__full_name",
        "patient__user__username",
        "family__name",
    ]

    autocomplete_fields = [
        "family",
        "patient",
    ]

    readonly_fields = [
        "created_at",
        "updated_at",
    ]
    