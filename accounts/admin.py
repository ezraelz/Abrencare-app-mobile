from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'username', 'email', 'account_status', 'address',
                  'first_name', 'last_name', 'phone_number',
                  'profile_picture']

    search_fields = ['username', 'email', 'first_name', 'last_name']
    list_filter = ['is_active', 'is_staff', 'date_joined']
    ordering = ['id']
    readonly_fields = ['date_joined']

