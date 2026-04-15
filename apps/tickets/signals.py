from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ticket
from .webpush import send_ticket_push_notification


@receiver(post_save, sender=Ticket)
def notify_new_ticket(sender, instance, created, **kwargs):
    if not created:
        return
    transaction.on_commit(lambda: send_ticket_push_notification(instance))
