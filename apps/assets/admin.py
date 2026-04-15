from django.contrib import admin
from .models import Asset, AssetHistory


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_tag', 'asset_type', 'brand', 'model', 'status', 'assigned_to_requester', 'assigned_to_staff']
    list_filter = ['asset_type', 'status']
    search_fields = ['asset_tag', 'brand', 'model', 'serial_number']
    ordering = ['asset_tag']


@admin.register(AssetHistory)
class AssetHistoryAdmin(admin.ModelAdmin):
    list_display = ['asset', 'action', 'performed_by', 'created_at']
    list_filter = ['action']
    readonly_fields = ['created_at']
