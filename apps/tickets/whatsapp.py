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


def send_whatsapp_template_message(to, template_name, language_code='pt_BR', components=None):
    if not settings.WHATSAPP_MESSAGES_URL:
        raise WhatsAppAPIError('WHATSAPP_MESSAGES_URL nao configurado.')

    template = {
        'name': template_name,
        'language': {'code': language_code},
    }
    if components:
        template['components'] = components

    payload = {
        'messaging_product': 'whatsapp',
        'to': to,
        'type': 'template',
        'template': template,
    }

    http_request = request.Request(
        settings.WHATSAPP_MESSAGES_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers=build_whatsapp_headers(),
        method='POST',
    )

    with request.urlopen(http_request, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))


def send_ticket_feedback_template(to, ticket):
    ticket_short_number = ticket.ticket_number.split('-')[-1]
    components = [
        {
            'type': 'header',
            'parameters': [{'type': 'text', 'text': ticket_short_number}],
        },
        {
            'type': 'body',
            'parameters': [{'type': 'text', 'text': ticket.title}],
        },
    ]
    return send_whatsapp_template_message(to, 'feedback_ticket', components=components)
