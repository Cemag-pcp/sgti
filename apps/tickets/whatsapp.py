import json
from urllib import request

from django.conf import settings


class WhatsAppAPIError(Exception):
    pass


def build_whatsapp_headers():
    if not settings.WHATSAPP_ACCESS_TOKEN:
        raise WhatsAppAPIError('WHATSAPP_ACCESS_TOKEN nao configurado.')

    return {
        'Authorization': f'Bearer {settings.WHATSAPP_ACCESS_TOKEN}',
        'Content-Type': 'application/json',
    }


def send_whatsapp_text_message(to, body):
    if not settings.WHATSAPP_MESSAGES_URL:
        raise WhatsAppAPIError('WHATSAPP_MESSAGES_URL nao configurado.')

    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'text',
        'text': {'body': body},
    }

    http_request = request.Request(
        settings.WHATSAPP_MESSAGES_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers=build_whatsapp_headers(),
        method='POST',
    )

    with request.urlopen(http_request, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))
