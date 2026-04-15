from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['name', 'app_type', 'responsible', 'release_date', 'is_active', 'updated_at']
    list_filter = ['app_type', 'is_active']
    search_fields = ['name', 'responsible', 'description']
