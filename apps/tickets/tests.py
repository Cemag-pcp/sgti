import json
from unittest.mock import patch
from django.db import transaction
from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser, RequesterProfile
from apps.tickets.models import BrowserPushSubscription, Device, Location, Ticket, WhatsAppConversation
from apps.tickets.whatsapp import (
    WhatsAppAPIError,
    build_whatsapp_headers,
    send_whatsapp_text_message,
)
from apps.tickets.webpush import get_vapid_private_key
from apps.tickets.whatsapp_bot import process_incoming_whatsapp_message
from datetime import timedelta


class WhatsAppServiceTests(SimpleTestCase):
    @override_settings(WHATSAPP_ACCESS_TOKEN='test-token')
    def test_build_headers_uses_bearer_token(self):
        headers = build_whatsapp_headers()

        self.assertEqual(headers['Authorization'], 'Bearer test-token')
        self.assertEqual(headers['Content-Type'], 'application/json')

    @override_settings(WHATSAPP_ACCESS_TOKEN='')
    def test_build_headers_requires_access_token(self):
        with self.assertRaisesMessage(
            WhatsAppAPIError,
            'WHATSAPP_ACCESS_TOKEN nao configurado.',
        ):
            build_whatsapp_headers()

    @override_settings(
        WHATSAPP_ACCESS_TOKEN='test-token',
        WHATSAPP_MESSAGES_URL='https://graph.facebook.com/v20.0/123/messages',
    )
    @patch('apps.tickets.whatsapp.request.urlopen')
    def test_send_text_message_posts_expected_payload(self, mock_urlopen):
        response_data = {'messages': [{'id': 'wamid.test'}]}
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')

        result = send_whatsapp_text_message('5511999999999', 'Teste de envio')

        self.assertEqual(result, response_data)
        http_request = mock_urlopen.call_args.args[0]
        self.assertEqual(http_request.full_url, 'https://graph.facebook.com/v20.0/123/messages')
        self.assertEqual(http_request.get_method(), 'POST')
        self.assertEqual(
            json.loads(http_request.data.decode('utf-8')),
            {
                'messaging_product': 'whatsapp',
                'to': '5511999999999',
                'type': 'text',
                'text': {'body': 'Teste de envio'},
            },
        )
        self.assertEqual(http_request.headers['Authorization'], 'Bearer test-token')


class WhatsAppWebhookTests(SimpleTestCase):
    def test_get_verification_returns_challenge_with_valid_token(self):
        with override_settings(WHATSAPP_VERIFY_TOKEN='verify-token'):
            response = self.client.get(
                reverse('tickets:whatsapp_webhook'),
                {
                    'hub.mode': 'subscribe',
                    'hub.verify_token': 'verify-token',
                    'hub.challenge': 'abc123',
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'abc123')

    def test_get_verification_rejects_invalid_token(self):
        with override_settings(WHATSAPP_VERIFY_TOKEN='verify-token'):
            response = self.client.get(
                reverse('tickets:whatsapp_webhook'),
                {
                    'hub.mode': 'subscribe',
                    'hub.verify_token': 'wrong-token',
                    'hub.challenge': 'abc123',
                },
            )

        self.assertEqual(response.status_code, 403)

    def test_post_rejects_invalid_json(self):
        response = self.client.post(
            reverse('tickets:whatsapp_webhook'),
            data='{"object": ',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 'invalid_json'})


class WebPushConfigTests(SimpleTestCase):
    @override_settings(
        WEBPUSH_VAPID_PRIVATE_KEY=(
            '-----BEGIN PRIVATE KEY-----'
            'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgifpgeZDkesBeBJ7D'
            'JTyGmhyYF0OSzZH7EoZPwhu21tOhRANCAAQB8FCgvdMSK2Q0RwutYC6SesTFOnKk'
            '6mbTDqZsXYYq1O5FQNi1pv0I5wkuMuAmlI1V61zcT8l17xgWuUNeiaCv'
            '-----END PRIVATE KEY-----'
        )
    )
    def test_get_vapid_private_key_normalizes_inline_pem(self):
        normalized = get_vapid_private_key()

        self.assertTrue(normalized.startswith('MIGHAgEAMBMG'))
        self.assertNotIn('PRIVATE KEY', normalized)
        self.assertNotIn('\n', normalized)

    def test_get_vapid_private_key_reads_pem_file_path(self):
        pem_content = '\n'.join(
            [
                '-----BEGIN PRIVATE KEY-----',
                'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgifpgeZDkesBeBJ7D',
                'JTyGmhyYF0OSzZH7EoZPwhu21tOhRANCAAQB8FCgvdMSK2Q0RwutYC6SesTFOnKk',
                '6mbTDqZsXYYq1O5FQNi1pv0I5wkuMuAmlI1V61zcT8l17xgWuUNeiaCv',
                '-----END PRIVATE KEY-----',
            ]
        )

        with TemporaryDirectory() as temp_dir:
            pem_path = Path(temp_dir) / 'webpush.pem'
            pem_path.write_text(pem_content, encoding='utf-8')

            with override_settings(WEBPUSH_VAPID_PRIVATE_KEY=str(pem_path)):
                self.assertEqual(
                    get_vapid_private_key(),
                    (
                        'MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgifpgeZDkesBeBJ7D'
                        'JTyGmhyYF0OSzZH7EoZPwhu21tOhRANCAAQB8FCgvdMSK2Q0RwutYC6SesTFOnKk'
                        '6mbTDqZsXYYq1O5FQNi1pv0I5wkuMuAmlI1V61zcT8l17xgWuUNeiaCv'
                    ),
                )


class TicketCreateApiTests(TestCase):
    def setUp(self):
        self.location = Location.objects.create(name='TI')
        self.device = Device.objects.create(name='Notebook')
        self.inactive_device = Device.objects.create(name='Desktop', is_active=False)

    def test_api_lists_only_active_devices(self):
        response = self.client.get(reverse('tickets:api_devices'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                'devices': [
                    {
                        'id': self.device.id,
                        'name': 'Notebook',
                        'description': '',
                    }
                ]
            },
        )

    def test_api_creates_ticket_with_requester_contacts(self):
        payload = {
            'matricula': '12345',
            'requester_name': 'Maria Silva',
            'requester_email': 'maria@empresa.com',
            'requester_phone': '1133334444',
            'requester_whatsapp_phone': '5511999999999',
            'title': 'Notebook sem ligar',
            'description': 'O equipamento nao liga desde cedo.',
            'category': Ticket.HARDWARE,
            'priority': Ticket.HIGH,
            'location_name': 'TI',
            'device_name': 'Notebook',
        }

        response = self.client.post(
            reverse('tickets:api_open'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        body = response.json()
        requester = RequesterProfile.objects.get(matricula='12345')
        ticket = Ticket.objects.get(pk=body['ticket']['id'])

        self.assertEqual(body['status'], 'created')
        self.assertEqual(ticket.requester, requester)
        self.assertEqual(ticket.location, self.location)
        self.assertEqual(ticket.device, self.device)
        self.assertEqual(ticket.priority, Ticket.HIGH)
        self.assertEqual(requester.email, 'maria@empresa.com')
        self.assertEqual(requester.phone, '1133334444')
        self.assertEqual(requester.whatsapp_phone, '5511999999999')

    def test_api_accepts_device_and_location_alias_fields(self):
        payload = {
            'matricula': '54321',
            'requester_name': 'Joao Souza',
            'title': 'Problema no desktop',
            'description': 'O equipamento nao inicializa corretamente.',
            'location': str(self.location.id),
            'device': str(self.device.id),
        }

        response = self.client.post(
            reverse('tickets:api_open'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        ticket = Ticket.objects.get(pk=response.json()['ticket']['id'])
        self.assertEqual(ticket.location, self.location)
        self.assertEqual(ticket.device, self.device)

    def test_api_returns_validation_errors(self):
        response = self.client.post(
            reverse('tickets:api_open'),
            data=json.dumps({'matricula': '12345'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'validation_error')

    def test_api_rejects_invalid_json_payload(self):
        response = self.client.post(
            reverse('tickets:api_open'),
            data='{"matricula": ',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'error': 'invalid_json'})

    def test_api_returns_validation_error_when_asset_tag_is_not_found(self):
        payload = {
            'matricula': '12345',
            'requester_name': 'Maria Silva',
            'title': 'Notebook sem ligar',
            'description': 'O equipamento nao liga desde cedo.',
            'location_id': self.location.id,
            'device_id': self.device.id,
            'asset_tag': 'AT-9999',
        }

        response = self.client.post(
            reverse('tickets:api_open'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertEqual(body['error'], 'validation_error')
        self.assertIn('asset_tag', body['errors'])
        self.assertFalse(Ticket.objects.filter(title='Notebook sem ligar').exists())

    @patch('apps.tickets.views.create_ticket_from_submission')
    def test_api_returns_json_for_unexpected_internal_error(self, mock_create_ticket):
        mock_create_ticket.side_effect = RuntimeError('simulated failure')
        payload = {
            'matricula': '12345',
            'requester_name': 'Maria Silva',
            'title': 'Notebook sem ligar',
            'description': 'O equipamento nao liga desde cedo.',
            'location_id': self.location.id,
            'device_id': self.device.id,
        }

        response = self.client.post(
            reverse('tickets:api_open'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()['error'], 'internal_error')
        self.assertEqual(response.json()['detail'], 'simulated failure')


class TicketNotificationsPollTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='notifier@example.com',
            password='12345678',
            full_name='Notifier User',
            role=CustomUser.TECHNICIAN,
        )
        self.requester = RequesterProfile.objects.create(
            matricula='77777',
            full_name='Solicitante Teste',
        )

    def test_poll_requires_since_to_return_tickets(self):
        self.client.force_login(self.user)
        Ticket.objects.create(
            requester=self.requester,
            title='Sem referencia',
            description='Teste sem since',
        )

        response = self.client.get(reverse('tickets:notifications_poll'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['tickets'], [])
        self.assertIn('server_time', response.json())

    def test_poll_returns_new_tickets_after_given_timestamp(self):
        self.client.force_login(self.user)
        reference = timezone.now() - timedelta(minutes=1)
        ticket = Ticket.objects.create(
            requester=self.requester,
            title='Novo chamado monitorado',
            description='Teste de polling',
            priority=Ticket.HIGH,
        )

        response = self.client.get(
            reverse('tickets:notifications_poll'),
            {'since': reference.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body['tickets']), 1)
        self.assertEqual(body['tickets'][0]['id'], ticket.id)
        self.assertEqual(body['tickets'][0]['ticket_number'], ticket.ticket_number)
        self.assertEqual(body['tickets'][0]['priority'], Ticket.HIGH)
        self.assertIn('server_time', body)


class PushSubscriptionTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='push@example.com',
            password='12345678',
            full_name='Push User',
            role=CustomUser.TECHNICIAN,
        )

    def test_subscribe_creates_subscription(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('tickets:push_subscription'),
            data=json.dumps(
                {
                    'endpoint': 'https://example.com/push/123',
                    'keys': {
                        'p256dh': 'test-p256dh',
                        'auth': 'test-auth',
                    },
                }
            ),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        subscription = BrowserPushSubscription.objects.get(endpoint='https://example.com/push/123')
        self.assertEqual(subscription.user, self.user)
        self.assertTrue(subscription.is_active)

    def test_delete_marks_subscription_inactive(self):
        self.client.force_login(self.user)
        BrowserPushSubscription.objects.create(
            user=self.user,
            endpoint='https://example.com/push/123',
            p256dh='test-p256dh',
            auth='test-auth',
        )

        response = self.client.delete(
            reverse('tickets:push_subscription'),
            data=json.dumps({'endpoint': 'https://example.com/push/123'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(BrowserPushSubscription.objects.get(endpoint='https://example.com/push/123').is_active)


class TicketWebPushSignalTests(TestCase):
    @patch('apps.tickets.signals.send_ticket_push_notification')
    def test_ticket_creation_triggers_webpush_after_commit(self, mock_send):
        requester = RequesterProfile.objects.create(
            matricula='99123',
            full_name='Signal Test',
        )

        with transaction.atomic():
            ticket = Ticket.objects.create(
                requester=requester,
                title='Chamado com push',
                description='Teste de envio web push',
            )
            self.assertFalse(mock_send.called)

        mock_send.assert_called_once_with(ticket)


class WhatsAppBotFlowTests(TestCase):
    def test_bot_opens_ticket_after_collecting_required_fields(self):
        first_reply = process_incoming_whatsapp_message('5511999999999', 'abrir chamado')
        second_reply = process_incoming_whatsapp_message('5511999999999', '12345')
        third_reply = process_incoming_whatsapp_message('5511999999999', 'Maria Silva')
        fourth_reply = process_incoming_whatsapp_message('5511999999999', 'Notebook sem ligar')
        fifth_reply = process_incoming_whatsapp_message(
            '5511999999999',
            'O equipamento nao liga desde hoje cedo.',
        )

        requester = RequesterProfile.objects.get(matricula='12345')
        ticket = Ticket.objects.get(requester=requester)
        conversation = WhatsAppConversation.objects.get(phone_number='5511999999999')

        self.assertEqual(first_reply, 'Informe sua matricula para abrir o chamado.')
        self.assertIn('nome completo', second_reply.lower())
        self.assertIn('titulo curto', third_reply.lower())
        self.assertIn('descreva o problema', fourth_reply.lower())
        self.assertIn(ticket.ticket_number, fifth_reply)
        self.assertEqual(requester.full_name, 'Maria Silva')
        self.assertEqual(requester.whatsapp_phone, '5511999999999')
        self.assertEqual(ticket.title, 'Notebook sem ligar')
        self.assertEqual(ticket.description, 'O equipamento nao liga desde hoje cedo.')
        self.assertEqual(conversation.state, WhatsAppConversation.COMPLETED)

    def test_existing_requester_skips_name_step(self):
        RequesterProfile.objects.create(
            matricula='54321',
            full_name='Joao Souza',
            whatsapp_phone='5511888888888',
        )

        process_incoming_whatsapp_message('5511888888888', 'abrir chamado')
        reply = process_incoming_whatsapp_message('5511888888888', '54321')

        conversation = WhatsAppConversation.objects.get(phone_number='5511888888888')

        self.assertIn('Joao Souza', reply)
        self.assertEqual(conversation.state, WhatsAppConversation.AWAITING_TITLE)

    @patch('apps.tickets.views.send_whatsapp_text_message')
    def test_webhook_processes_message_and_sends_reply(self, mock_send_whatsapp):
        payload = {
            'object': 'whatsapp_business_account',
            'entry': [
                {
                    'changes': [
                        {
                            'value': {
                                'contacts': [{'profile': {'name': 'Maria Silva'}}],
                                'messages': [
                                    {
                                        'from': '5511999999999',
                                        'text': {'body': 'abrir chamado'},
                                    }
                                ],
                            }
                        }
                    ]
                }
            ],
        }

        response = self.client.post(
            reverse('tickets:whatsapp_webhook'),
            data=json.dumps(payload),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {
                'status': 'received',
                'object': 'whatsapp_business_account',
                'processed_messages': 1,
            },
        )
        mock_send_whatsapp.assert_called_once_with(
            '5511999999999',
            'Informe sua matricula para abrir o chamado.',
        )
