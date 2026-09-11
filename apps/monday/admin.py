from django.contrib import admin

from .models import MondaySubitemTicket


@admin.register(MondaySubitemTicket)
class MondaySubitemTicketAdmin(admin.ModelAdmin):
    list_display = ['monday_subitem_id', 'ticket', 'created_by', 'created_at']
    readonly_fields = ['created_at']
