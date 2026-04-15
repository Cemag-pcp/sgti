import json
import logging

from django.conf import settings
from django.utils import timezone

from pywebpush import WebPushException, webpush

from .models import BrowserPushSubscription


logger = logging.getLogger(__name__)


def webpush_is_configured():
    return bool(settings.WEBPUSH_VAPID_PUBLIC_KEY and settings.WEBPUSH_VAPID_PRIVATE_KEY)


def build_ticket_push_payload(ticket):
    priority_label = dict(ticket.PRIORITY_CHOICES).get(ticket.priority, ticket.priority)
    return {
        'title': f'Novo chamado - {ticket.ticket_number}',
        'body': f'{ticket.title}\nPrioridade: {priority_label}',
        'tag': f'ticket-{ticket.id}',
        'url': f'/tickets/{ticket.id}/',
    }


def send_ticket_push_notification(ticket):
    if not webpush_is_configured():
        return 0

    subscriptions = BrowserPushSubscription.objects.filter(
        is_active=True,
        user__is_active=True,
        user__role__in=['SUPERVISOR', 'TECHNICIAN'],
    ).select_related('user')

    payload = json.dumps(build_ticket_push_payload(ticket))
    sent = 0

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    'endpoint': subscription.endpoint,
                    'keys': {
                        'p256dh': subscription.p256dh,
                        'auth': subscription.auth,
                    },
                },
                data=payload,
                vapid_private_key=settings.WEBPUSH_VAPID_PRIVATE_KEY,
                vapid_claims={'sub': f'mailto:{settings.WEBPUSH_VAPID_ADMIN_EMAIL}'},
            )
            subscription.last_success_at = timezone.now()
            subscription.save(update_fields=['last_success_at', 'updated_at'])
            sent += 1
        except WebPushException as exc:
            status_code = getattr(getattr(exc, 'response', None), 'status_code', None)
            if status_code in {404, 410}:
                subscription.is_active = False
                subscription.save(update_fields=['is_active', 'updated_at'])
            logger.warning('Failed to send web push for subscription %s: %s', subscription.pk, exc)

    return sent
