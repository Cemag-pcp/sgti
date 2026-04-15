from django.contrib import admin
from .models import Ticket, TimeEntry, TicketObservation, StatusHistory, SLAConfig, Location


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['ticket_number', 'title', 'requester', 'priority', 'status', 'assigned_to', 'created_at']
    list_filter = ['status', 'priority', 'category']
    search_fields = ['ticket_number', 'title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['ticket_number', 'created_at', 'updated_at']


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'technician', 'started_at', 'ended_at', 'duration_minutes']
    list_filter = ['technician']


@admin.register(TicketObservation)
class TicketObservationAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal']


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['ticket', 'changed_by', 'old_status', 'new_status', 'changed_at']
    readonly_fields = ['changed_at']


@admin.register(SLAConfig)
class SLAConfigAdmin(admin.ModelAdmin):
    list_display = ['priority', 'resolution_hours', 'is_active', 'updated_at']
    readonly_fields = ['updated_at']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
