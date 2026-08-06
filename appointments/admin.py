from django.contrib import admin
from .models import Appointment, Scheduling

@admin.register(Scheduling)
class SchedulingAdmin(admin.ModelAdmin):
    list_display = [
            "id",
            "doctor",
            "day",
            "start_time",
            "end_time",
            "is_available",
            "created_at",
        ]

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
            "id",
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time",
            "status",
            "reason",
            "created_at",
        ]
