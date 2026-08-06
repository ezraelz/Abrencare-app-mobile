from django.contrib import admin
from .models import Doctor

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display =[ 
                "id",
                "user",
                "specialization",
                "license_number",
                "years_of_experience",
                "consultation_fee",
                "verified",
                "created_at",]
    
