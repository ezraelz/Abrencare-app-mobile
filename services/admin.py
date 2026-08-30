from django.contrib import admin
from .models import Service, Feature

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']
    ordering = ['id']

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'service_for', 'description', 'created_at']
    search_fields = ['name', 'service_for']
    list_filter = ['created_at']
    ordering = ['id']
