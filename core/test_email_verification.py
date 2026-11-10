import re
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from core.email_verification import send_verification_code
from core.models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='novo@example.com', password='StrongPass123!')

    def code(self):
        send_verification_code(self.user)
        return re.search(r'\b[0-9]{6}\b', mail.outbox[-1].body).group()

    def verify(self, code):
        return self.client.post('/api/verificar-email/', {'email': self.user.email, 'codigo': code})

    def test_pending_account_cannot_login(self):
        response = self.client.post('/api/token/', {'email': self.user.email, 'password': 'StrongPass123!'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['code'], 'email_not_verified')

    def test_verification_issues_custom_tokens_and_cannot_be_reused(self):
        code = self.code()
        self.assertNotEqual(self.user.verification_code_hash, code)
        response = self.verify(code)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AccessToken(response.data['access'])['email'], self.user.email)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertEqual(self.user.verification_code_hash, '')
        self.assertEqual(self.verify(code).status_code, 400)
        login = self.client.post('/api/token/', {'email': self.user.email, 'password': 'StrongPass123!'})
        self.assertEqual(login.status_code, 200)

    def test_wrong_attempts_are_persisted_and_limited(self):
        code = self.code()
        wrong = '999999' if code != '999999' else '000000'
        for _ in range(5):
            self.assertEqual(self.verify(wrong).status_code, 400)
        self.user.refresh_from_db()
        self.assertEqual(self.user.verification_attempts, 5)
        self.assertEqual(self.verify(code).status_code, 429)

    def test_expired_code_is_rejected(self):
        code = self.code()
        User.objects.filter(pk=self.user.pk).update(verification_code_created_at=timezone.now()-timedelta(minutes=11))
        self.assertEqual(self.verify(code).status_code, 400)

    def test_resend_cooldown_and_expiry_reset(self):
        self.code()
        data = {'email': self.user.email}
        self.assertEqual(self.client.post('/api/reenviar-codigo/', data).status_code, 429)
        User.objects.filter(pk=self.user.pk).update(verification_attempts=5, verification_code_created_at=timezone.now()-timedelta(minutes=11))
        self.assertEqual(self.client.post('/api/reenviar-codigo/', data).status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.verification_attempts, 0)
        self.assertEqual(len(mail.outbox), 2)

    def test_resend_does_not_reset_attempt_limit_early(self):
        self.code()
        User.objects.filter(pk=self.user.pk).update(verification_attempts=5, verification_code_created_at=timezone.now()-timedelta(minutes=2))
        self.assertEqual(self.client.post('/api/reenviar-codigo/', {'email': self.user.email}).status_code, 429)

    def test_non_numeric_code_is_rejected(self):
        self.assertEqual(self.verify('abcdef').status_code, 400)

    def test_registration_sends_email_for_both_profiles(self):
        for route, extra, tipo in [('alunos', {}, 'aluno'), ('professores', {'cpf': '12345678901', 'telefone': '47999999999'}, 'professor')]:
            with self.subTest(route=route):
                data = {'email': f'{route}@example.com', 'name': 'Novo', 'username': route, 'password': 'StrongPass123!', 'data_nascimento': '2000-01-01', 'email_verificado': True, **extra}
                with self.captureOnCommitCallbacks(execute=True):
                    response = self.client.post(f'/api/{route}/', data)
                self.assertEqual(response.status_code, 201, response.data)
                user = User.objects.get(email=data['email'])
                self.assertFalse(user.email_verified)
                code = re.search(r'\b[0-9]{6}\b', mail.outbox[-1].body).group()
                response = self.client.post('/api/verificar-email/', {'email': user.email, 'codigo': code})
                self.assertEqual(response.status_code, 200, response.data)
                token = AccessToken(response.data['access'])
                self.assertEqual(token['tipo'], tipo)
                self.assertIn(f'{tipo}_id', token)
                profile = getattr(user, f'{tipo}_profile')
                self.assertTrue(profile.email_verificado)

    @patch('core.email_verification.send_mail', side_effect=OSError('SMTP unavailable'))
    def test_smtp_failure_keeps_account_pending(self, _send):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/api/alunos/', {'email': 'smtp@example.com', 'name': 'Novo', 'username': 'novo', 'password': 'StrongPass123!', 'data_nascimento': '2000-01-01'})
        self.assertEqual(response.status_code, 201)
        self.assertFalse(User.objects.get(email='smtp@example.com').email_verified)
