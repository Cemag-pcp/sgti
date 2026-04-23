from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import CustomUser


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@example.com',
    APP_BASE_URL='https://sgti.example.com',
)
class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='tecnico@example.com',
            password='SenhaAtual123!',
            full_name='Tecnico Teste',
        )

    def test_password_reset_sends_email_with_reset_link(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'email': self.user.email},
        )

        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, [self.user.email])
        self.assertEqual(sent_email.from_email, 'noreply@example.com')
        self.assertIn('Redefinição de senha SGTI', sent_email.subject)
        self.assertIn('https://sgti.example.com/accounts/reset/', sent_email.body)

    def test_password_can_be_reset_from_valid_token(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        response = self.client.post(
            reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token}),
            {
                'new_password1': 'NovaSenha123@',
                'new_password2': 'NovaSenha123@',
            },
        )

        self.assertRedirects(response, reverse('accounts:password_reset_complete'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NovaSenha123@'))
