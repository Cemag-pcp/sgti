from django.contrib import admin
from .models import SoftwareRequest


@admin.register(SoftwareRequest)
class SoftwareRequestAdmin(admin.ModelAdmin):
    list_display = ['request_number', 'software_name', 'requester_name', 'setor', 'stage', 'created_at']
    list_filter = ['stage', 'needs_director_approval', 'created_at']
    search_fields = ['request_number', 'software_name', 'requester_name', 'setor', 'matricula']
    readonly_fields = ['request_number', 'created_at', 'updated_at']
