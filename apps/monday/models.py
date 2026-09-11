from django.conf import settings
from django.db import models


class MondaySubitemTicket(models.Model):
    """Rastreia subelementos do Monday já convertidos em chamados do SGTI (evita duplicidade)."""
    monday_subitem_id = models.CharField(max_length=50, unique=True, verbose_name='Subelemento (Monday)')
    ticket = models.ForeignKey(
        'tickets.Ticket',
        on_delete=models.CASCADE,
        related_name='monday_subitem_links',
        verbose_name='Chamado',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Convertido por',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Vínculo Monday -> Ticket'
        verbose_name_plural = 'Vínculos Monday -> Ticket'

    def __str__(self):
        return f'Subelemento {self.monday_subitem_id} -> {self.ticket.ticket_number}'
