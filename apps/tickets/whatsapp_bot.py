from django.db import transaction

from apps.accounts.models import RequesterProfile

from .models import Ticket, WhatsAppConversation


START_COMMANDS = {
    'abrir chamado',
    'novo chamado',
    'chamado',
    'abrir ticket',
    'ticket',
}


def extract_whatsapp_messages(payload):
    incoming_messages = []
    for entry in payload.get('entry', []):
        for change in entry.get('changes', []):
            value = change.get('value', {})
            contacts = value.get('contacts', [])
            profile_name = ''
            if contacts:
                profile_name = contacts[0].get('profile', {}).get('name', '')

            for message in value.get('messages', []):
                text_body = message.get('text', {}).get('body', '').strip()
                sender = message.get('from', '').strip()
                if sender and text_body:
                    incoming_messages.append(
                        {
                            'from': sender,
                            'text': text_body,
                            'profile_name': profile_name,
                        }
                    )
    return incoming_messages


def process_incoming_whatsapp_message(phone_number, text, profile_name=''):
    normalized_text = text.strip()
    lowered_text = normalized_text.lower()

    with transaction.atomic():
        conversation, _ = WhatsAppConversation.objects.select_for_update().get_or_create(
            phone_number=phone_number,
            defaults={'context': {}},
        )
        context = conversation.context or {}

        if lowered_text in {'cancelar', 'reiniciar', 'resetar'}:
            conversation.state = WhatsAppConversation.AWAITING_COMMAND
            conversation.context = {}
            conversation.save(update_fields=['state', 'context', 'last_message_at'])
            return (
                'Fluxo reiniciado. Envie "abrir chamado" para começar um novo atendimento.'
            )

        if conversation.state in {
            WhatsAppConversation.AWAITING_COMMAND,
            WhatsAppConversation.COMPLETED,
        }:
            if lowered_text not in START_COMMANDS:
                return (
                    'Para abrir um chamado, envie "abrir chamado". '
                    'Se quiser reiniciar o fluxo, envie "cancelar".'
                )
            conversation.state = WhatsAppConversation.AWAITING_MATRICULA
            conversation.context = {}
            conversation.save(update_fields=['state', 'context', 'last_message_at'])
            return 'Informe sua matricula para abrir o chamado.'

        if conversation.state == WhatsAppConversation.AWAITING_MATRICULA:
            requester = RequesterProfile.objects.filter(matricula=normalized_text).first()
            context['matricula'] = normalized_text
            if requester:
                context['full_name'] = requester.full_name
                conversation.state = WhatsAppConversation.AWAITING_TITLE
                conversation.context = context
                conversation.save(update_fields=['state', 'context', 'last_message_at'])
                return (
                    f'Identifiquei {requester.full_name}. '
                    'Agora informe um titulo curto para o chamado.'
                )

            conversation.state = WhatsAppConversation.AWAITING_NAME
            conversation.context = context
            conversation.save(update_fields=['state', 'context', 'last_message_at'])
            suggested_name = profile_name.strip()
            if suggested_name:
                return (
                    f'Nao encontrei sua matricula no cadastro. '
                    f'Confirme seu nome completo. Exemplo: {suggested_name}'
                )
            return 'Nao encontrei sua matricula no cadastro. Informe seu nome completo.'

        if conversation.state == WhatsAppConversation.AWAITING_NAME:
            context['full_name'] = normalized_text
            conversation.state = WhatsAppConversation.AWAITING_TITLE
            conversation.context = context
            conversation.save(update_fields=['state', 'context', 'last_message_at'])
            return 'Perfeito. Informe agora um titulo curto para o chamado.'

        if conversation.state == WhatsAppConversation.AWAITING_TITLE:
            context['title'] = normalized_text
            conversation.state = WhatsAppConversation.AWAITING_DESCRIPTION
            conversation.context = context
            conversation.save(update_fields=['state', 'context', 'last_message_at'])
            return 'Descreva o problema com mais detalhes.'

        if conversation.state == WhatsAppConversation.AWAITING_DESCRIPTION:
            context['description'] = normalized_text

            requester, _ = RequesterProfile.objects.get_or_create(
                matricula=context['matricula'],
                defaults={
                    'full_name': context['full_name'],
                    'whatsapp_phone': phone_number,
                },
            )

            updates = []
            if context.get('full_name') and requester.full_name != context['full_name']:
                requester.full_name = context['full_name']
                updates.append('full_name')
            if phone_number and requester.whatsapp_phone != phone_number:
                requester.whatsapp_phone = phone_number
                updates.append('whatsapp_phone')
            if updates:
                requester.save(update_fields=updates)

            ticket = Ticket.objects.create(
                requester=requester,
                title=context['title'],
                description=context['description'],
            )

            conversation.state = WhatsAppConversation.COMPLETED
            conversation.context = {'last_ticket_id': ticket.id, 'last_ticket_number': ticket.ticket_number}
            conversation.save(update_fields=['state', 'context', 'last_message_at'])
            return (
                f'Chamado {ticket.ticket_number} aberto com sucesso. '
                'Se quiser abrir outro, envie "abrir chamado".'
            )

        conversation.state = WhatsAppConversation.AWAITING_COMMAND
        conversation.context = {}
        conversation.save(update_fields=['state', 'context', 'last_message_at'])
        return 'Fluxo reiniciado. Envie "abrir chamado" para comecar.'
