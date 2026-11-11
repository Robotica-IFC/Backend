import re
from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core.email_verification import send_verification_code
from core.models import User


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class PasswordResetTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='recuperar@example.com', password='OriginalPass123!', email_verified=True,
        )

    def request_code(self, email=None):
        return self.client.post('/api/recuperar-senha/', {'email': email or self.user.email})

    def code(self):
        response = self.request_code()
        self.assertEqual(response.status_code, 200, response.data)
        return re.search(r'\b[0-9]{6}\b', mail.outbox[-1].body).group()

    def verify(self, code, email=None):
        return self.client.post('/api/recuperar-senha/verificar-codigo/', {
            'email': email or self.user.email, 'codigo': code,
        })

    def reset(self, token, password='NewStrongPass456!', confirmation=None, email=None):
        return self.client.post('/api/redefinir-senha/', {
            'email': email or self.user.email, 'token': token,
            'password': password, 'confirm_password': password if confirmation is None else confirmation,
        })

    def expire(self):
        User.objects.filter(pk=self.user.pk).update(
            password_reset_created_at=timezone.now() - timedelta(minutes=11),
        )

    def test_complete_flow_changes_password_and_consumes_code_and_token(self):
        code = self.code()
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.password_reset_code_hash, code)
        self.assertEqual(mail.outbox[-1].subject, 'Redefina sua senha')
        self.assertIn('recuperação', mail.outbox[-1].alternatives[0].content)
        response = self.verify(code)
        self.assertEqual(response.status_code, 200, response.data)
        token = response.data['token']
        self.assertEqual(self.verify(code).status_code, 400)
        self.assertEqual(self.reset(token).status_code, 200)
        self.assertEqual(self.reset(token).status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass456!'))
        self.assertFalse(self.user.check_password('OriginalPass123!'))
        self.assertEqual(self.user.password_reset_token_hash, '')
        self.assertIsNone(self.user.password_reset_created_at)
        self.assertEqual(self.client.post('/api/token/', {
            'email': self.user.email, 'password': 'NewStrongPass456!',
        }).status_code, 200)

    def test_unknown_email_is_rejected_without_sending_code(self):
        response = self.request_code('naoexiste@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertIn('não está cadastrado', response.data['email'][0])
        self.assertEqual(len(mail.outbox), 0)
        self.assertEqual(self.verify('123456', 'naoexiste@example.com').status_code, 400)

    def test_inactive_email_is_rejected_without_sending_code(self):
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        response = self.request_code()
        self.assertEqual(response.status_code, 400)
        self.assertIn('inativa', response.data['email'][0])
        self.assertEqual(len(mail.outbox), 0)

    def test_request_code_accepts_registered_email_case_insensitively(self):
        self.assertEqual(self.request_code(self.user.email.upper()).status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[-1].to, [self.user.email])

    def test_email_is_case_insensitive(self):
        code = self.code()
        response = self.verify(code, self.user.email.upper())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.reset(response.data['token'], email=self.user.email.upper()).status_code, 200)

    def test_five_wrong_attempts_block_verification_and_resend_until_expiry(self):
        code = self.code()
        wrong = '999999' if code != '999999' else '000000'
        for _ in range(5):
            self.assertEqual(self.verify(wrong).status_code, 400)
        self.assertEqual(self.verify(code).status_code, 429)
        User.objects.filter(pk=self.user.pk).update(password_reset_created_at=timezone.now() - timedelta(minutes=2))
        self.assertEqual(self.request_code().status_code, 429)
        self.expire()
        self.assertEqual(self.request_code().status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.password_reset_attempts, 0)

    def test_expired_code_and_authorization_cannot_reset_password(self):
        code = self.code()
        self.expire()
        self.assertEqual(self.verify(code).status_code, 400)
        code = self.code()
        token = self.verify(code).data['token']
        self.expire()
        response = self.reset(token)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['code'], 'password_reset_expired')

    def test_resend_cooldown_and_old_code_invalidation(self):
        with patch('core.email_verification.secrets.randbelow', side_effect=[123456, 654321]):
            code = self.code()
            response = self.request_code()
            self.assertEqual(response.status_code, 429)
            self.assertGreater(response.data['retry_after'], 0)
            User.objects.filter(pk=self.user.pk).update(password_reset_created_at=timezone.now() - timedelta(minutes=2))
            new_code = self.code()
        self.assertEqual(self.verify(code).status_code, 400)
        self.assertEqual(self.verify(new_code).status_code, 200)

    def test_resend_preserves_failed_attempts_and_invalidates_authorization(self):
        token = self.verify(self.code()).data['token']
        User.objects.filter(pk=self.user.pk).update(
            password_reset_created_at=timezone.now() - timedelta(minutes=2), password_reset_attempts=2,
        )
        self.code()
        self.user.refresh_from_db()
        self.assertEqual(self.user.password_reset_attempts, 2)
        self.assertEqual(self.reset(token).status_code, 400)

    def test_reset_requires_correct_authorization_bound_to_email(self):
        token = self.verify(self.code()).data['token']
        other = User.objects.create_user(email='outra@example.com', password='OriginalPass123!')
        self.request_code(other.email)
        self.assertEqual(self.reset(token, email=other.email).status_code, 400)
        self.assertEqual(self.reset('forged').status_code, 400)
        self.assertEqual(self.reset('123456').status_code, 400)

    def test_password_mismatch_and_weak_password_keep_authorization_for_retry(self):
        token = self.verify(self.code()).data['token']
        response = self.reset(token, confirmation='DifferentPass789!')
        self.assertEqual(response.status_code, 400)
        self.assertIn('confirm_password', response.data)
        for password in ['short', '123456789', 'password', self.user.email]:
            with self.subTest(password=password):
                response = self.reset(token, password=password)
                self.assertEqual(response.status_code, 400)
                self.assertIn('password', response.data)
        self.assertEqual(self.reset(token).status_code, 200)

    def test_verification_and_recovery_codes_are_isolated(self):
        User.objects.filter(pk=self.user.pk).update(email_verified=False)
        self.user.refresh_from_db()
        with patch('core.email_verification.secrets.randbelow', side_effect=[123456, 654321]):
            send_verification_code(self.user)
            code = self.code()
        self.assertEqual(self.verify('123456').status_code, 400)
        self.assertEqual(self.client.post('/api/verificar-email/', {
            'email': self.user.email, 'codigo': code,
        }).status_code, 400)
        token = self.verify(code).data['token']
        self.assertEqual(self.reset(token).status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
        self.assertEqual(self.client.post('/api/verificar-email/', {
            'email': self.user.email, 'codigo': '123456',
        }).status_code, 200)

    @patch('core.email_verification.send_mail', side_effect=OSError('SMTP unavailable'))
    def test_delivery_failure_rolls_back_so_user_can_retry(self, _send):
        self.assertEqual(self.request_code().status_code, 503)
        self.user.refresh_from_db()
        self.assertEqual(self.user.password_reset_code_hash, '')
        self.assertIsNone(self.user.password_reset_created_at)

    def test_inactive_account_cannot_use_existing_code_or_authorization(self):
        code = self.code()
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        self.assertEqual(self.verify(code).status_code, 400)
        User.objects.filter(pk=self.user.pk).update(is_active=True)
        token = self.verify(code).data['token']
        User.objects.filter(pk=self.user.pk).update(is_active=False)
        self.assertEqual(self.reset(token).status_code, 400)

    def test_invalid_email_and_non_numeric_or_incomplete_code_are_rejected(self):
        self.assertEqual(self.request_code('not-an-email').status_code, 400)
        for code in ['12345', 'abcdef', '1234567', '12 456']:
            self.assertEqual(self.verify(code).status_code, 400)
