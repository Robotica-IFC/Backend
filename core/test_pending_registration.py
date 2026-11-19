import re
import uuid
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import check_password
from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import Aluno, CadastroPendente, Instituicao, Professor, User
from uploader.models import Image


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
    STORAGES={'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}},
)
class PendingRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def start(self, kind='aluno', email=None, **extra):
        return self.client.post({'aluno': '/api/alunos/', 'professor': '/api/professores/', 'usuario': '/api/registro/'}[kind], {
            'email': email or f'{kind}@example.test', 'name': 'Nova pessoa', 'username': 'nova_pessoa',
            'password': 'OriginalPass123!', 'data_nascimento': '2000-01-01', 'telefone': '47999999999',
            **extra,
        }, format='json')

    def code(self):
        return re.search(r'\b[0-9]{6}\b', mail.outbox[-1].body).group()

    def verify(self, registration, code=None, **extra):
        return self.client.post('/api/verificar-email/', {
            'email': registration['email'], 'registration_token': registration['registration_token'],
            'codigo': code or self.code(), **extra,
        })

    def resend(self, registration):
        return self.client.post('/api/reenviar-codigo/', {
            'email': registration['email'], 'registration_token': registration['registration_token'],
        })

    def assert_no_account(self):
        self.assertFalse(User.objects.exists())
        self.assertFalse(Aluno.objects.exists())
        self.assertFalse(Professor.objects.exists())

    def test_both_profiles_and_generic_registration_require_email_before_creating_account(self):
        for kind in ['aluno', 'professor', 'usuario']:
            with self.subTest(kind=kind):
                response = self.start(kind, email_verified=True, email_verificado=True)
                self.assertEqual(response.status_code, 202, response.data)
                self.assertTrue(response.data['verification_required'])
                self.assertNotIn('access', response.data)
                self.assertNotIn('refresh', response.data)
                self.assert_no_account()
                pending = CadastroPendente.objects.get(pk=response.data['registration_token'])
                self.assertNotIn('password', pending.dados)
                self.assertTrue(check_password('OriginalPass123!', pending.senha_hash))
                self.assertNotIn('OriginalPass123!', str(pending.dados))

    def test_correct_code_creates_verified_account_and_preserves_password_for_both_profiles(self):
        for kind in ['aluno', 'professor']:
            with self.subTest(kind=kind):
                registration = self.start(kind).data
                response = self.verify(registration)
                self.assertEqual(response.status_code, 200, response.data)
                self.assertTrue(response.data['registration_completed'])
                user = User.objects.get(email=registration['email'])
                self.assertTrue(user.email_verified)
                self.assertTrue(user.check_password('OriginalPass123!'))
                self.assertTrue(getattr(user, f'{kind}_profile').email_verificado)
                self.assertFalse(CadastroPendente.objects.filter(email=user.email).exists())
                self.assertEqual(self.client.post('/api/token/', {
                    'email': user.email, 'password': 'OriginalPass123!',
                }).status_code, 200)
                self.assertEqual(self.verify(registration, '123456').status_code, 400)
        self.assertEqual(User.objects.count(), 2)

    def test_pending_registration_cannot_login(self):
        registration = self.start().data
        response = self.client.post('/api/token/', {'email': registration['email'], 'password': 'OriginalPass123!'})
        self.assertEqual(response.status_code, 401)
        self.assertNotIn('access', response.data)
        self.assert_no_account()

    def test_registration_preserves_email_casing_for_subsequent_login(self):
        registration = self.start(email='Pessoa@example.test').data
        self.assertEqual(self.verify(registration).status_code, 200)
        response = self.client.post('/api/token/', {'email': 'Pessoa@example.test', 'password': 'OriginalPass123!'})
        self.assertEqual(response.status_code, 200, response.data)

    def test_incorrect_codes_are_limited_and_never_create_an_account(self):
        registration = self.start().data
        correct = self.code()
        wrong = '999999' if correct != '999999' else '000000'
        for _ in range(5):
            self.assertEqual(self.verify(registration, wrong).status_code, 400)
        self.assertEqual(self.verify(registration, correct).status_code, 429)
        self.assertEqual(CadastroPendente.objects.get(pk=registration['registration_token']).verification_attempts, 5)
        self.assert_no_account()

    def test_expired_code_can_be_resent_and_cannot_be_used_before_resend(self):
        with patch('core.email_verification.secrets.randbelow', side_effect=[123456, 654321]):
            registration = self.start().data
            old_code = self.code()
            CadastroPendente.objects.filter(pk=registration['registration_token']).update(
                verification_code_created_at=timezone.now() - timedelta(minutes=11), verification_attempts=5,
            )
            self.assertEqual(self.verify(registration, old_code).status_code, 400)
            self.assert_no_account()
            self.assertEqual(self.resend(registration).status_code, 200)
            self.assertEqual(self.verify(registration, old_code).status_code, 400)
            self.assert_no_account()
            self.assertEqual(self.verify(registration, self.code()).status_code, 200)

    def test_repeat_registration_recovers_existing_code_and_token_without_resending(self):
        first = self.start().data
        original_code = self.code()
        original_mail_count = len(mail.outbox)
        second = self.start()
        self.assertEqual(second.status_code, 202, second.data)
        self.assertEqual(second.data['registration_token'], first['registration_token'])
        self.assertEqual(len(mail.outbox), original_mail_count)
        self.assertEqual(CadastroPendente.objects.count(), 1)
        self.assert_no_account()
        self.assertEqual(self.verify(second.data, original_code).status_code, 200)
        self.assertTrue(User.objects.get(email=first['email']).email_verified)

    def test_repeat_registration_does_not_leak_token_for_wrong_password_or_profile(self):
        first = self.start().data
        invalid_password = self.start(password='DifferentPass456!')
        self.assertEqual(invalid_password.status_code, 429, invalid_password.data)
        self.assertNotIn('registration_token', invalid_password.data)
        invalid_profile = self.start('professor', email=first['email'])
        self.assertEqual(invalid_profile.status_code, 429, invalid_profile.data)
        self.assertNotIn('registration_token', invalid_profile.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(CadastroPendente.objects.count(), 1)
        self.assert_no_account()

    def test_resend_cooldown_preserves_attempts_and_does_not_create_account(self):
        registration = self.start().data
        self.assertEqual(self.resend(registration).status_code, 429)
        CadastroPendente.objects.filter(pk=registration['registration_token']).update(
            verification_code_created_at=timezone.now() - timedelta(minutes=2), verification_attempts=2,
        )
        self.assertEqual(self.resend(registration).status_code, 200)
        self.assertEqual(CadastroPendente.objects.get(pk=registration['registration_token']).verification_attempts, 2)
        self.assert_no_account()

    @patch('core.email_verification.send_mail', side_effect=OSError('SMTP unavailable'))
    def test_failed_email_delivery_creates_neither_account_nor_pending_record(self, _send):
        self.assertEqual(self.start().status_code, 503)
        self.assertFalse(CadastroPendente.objects.exists())
        self.assert_no_account()

    def test_failed_resend_preserves_previous_code_for_retry(self):
        registration = self.start().data
        CadastroPendente.objects.filter(pk=registration['registration_token']).update(
            verification_code_created_at=timezone.now() - timedelta(minutes=2),
        )
        original = CadastroPendente.objects.get(pk=registration['registration_token'])
        with patch('core.email_verification.send_mail', side_effect=OSError('SMTP unavailable')):
            self.assertEqual(self.resend(registration).status_code, 503)
        current = CadastroPendente.objects.get(pk=original.pk)
        self.assertEqual(current.verification_code_hash, original.verification_code_hash)
        self.assertEqual(current.verification_code_created_at, original.verification_code_created_at)
        self.assert_no_account()

    def test_verification_requires_matching_registration_token_and_email(self):
        registration = self.start().data
        code = self.code()
        self.assertEqual(self.client.post('/api/verificar-email/', {'email': registration['email'], 'codigo': code}).status_code, 400)
        self.assertEqual(self.verify(registration, code, registration_token=str(uuid.uuid4())).status_code, 400)
        self.assertEqual(self.verify(registration, code, email='other@example.test').status_code, 400)
        self.assert_no_account()

    def test_codes_from_different_registration_attempts_cannot_be_swapped(self):
        with patch('core.email_verification.secrets.randbelow', side_effect=[123456, 654321]):
            first = self.start().data
            first_code = self.code()
            CadastroPendente.objects.filter(pk=first['registration_token']).update(
                verification_code_created_at=timezone.now() - timedelta(minutes=2),
            )
            second = self.start(password='DifferentPass456!').data
            self.assertEqual(self.verify(first, self.code()).status_code, 400)
            self.assert_no_account()
            self.assertEqual(self.verify(first, first_code).status_code, 200)
            self.assertTrue(User.objects.get(email=first['email']).check_password('OriginalPass123!'))
            self.assertEqual(self.verify(second, self.code()).status_code, 400)
            self.assertEqual(User.objects.count(), 1)

    def test_expired_registration_never_creates_account_and_can_be_restarted(self):
        registration = self.start().data
        CadastroPendente.objects.filter(pk=registration['registration_token']).update(expira_em=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.verify(registration).data['code'], 'registration_expired')
        self.assertEqual(self.resend(registration).data['code'], 'registration_expired')
        self.assert_no_account()
        self.assertEqual(self.start().status_code, 202)
        self.assertFalse(CadastroPendente.objects.filter(pk=registration['registration_token']).exists())

    def test_generic_registration_is_only_completed_after_verification(self):
        registration = self.start('usuario').data
        self.assert_no_account()
        self.assertEqual(self.verify(registration).status_code, 200)
        self.assertTrue(User.objects.get(email=registration['email']).email_verified)

    def test_teacher_profile_fields_and_related_images_survive_temporary_storage(self):
        school = Instituicao.objects.create(nome='IFC', cidade='Araquari', estado='SC')
        image = Image.objects.create(file='images/avatar.png')
        registration = self.start(
            'professor', instituicao=str(school.pk), imagem_perfil=str(image.pk), cpf=None,
        ).data
        self.assert_no_account()
        self.assertEqual(self.verify(registration).status_code, 200)
        teacher = Professor.objects.get(user__email=registration['email'])
        self.assertEqual(teacher.instituicao_id, school.pk)
        self.assertEqual(teacher.imagem_perfil_id, image.pk)
        self.assertIsNone(teacher.cpf)
        self.assertEqual(teacher.telefone, '47999999999')
        self.assertEqual(teacher.data_nascimento.isoformat(), '2000-01-01')

    def test_legacy_unverified_user_cannot_use_access_or_refresh_tokens(self):
        user = User.objects.create_user(email='legacy@example.test', password='OriginalPass123!')
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        self.assertEqual(self.client.get('/api/usuarios/me/').status_code, 401)
        self.client.credentials()
        response = self.client.post('/api/token/refresh/', {'refresh': str(token)})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data['code'], 'email_not_verified')
        self.assertNotIn('access', response.data)

    def test_users_endpoint_cannot_bypass_registration_verification(self):
        user = User.objects.create_user(email='verified@example.test', email_verified=True)
        self.client.force_authenticate(user)
        response = self.client.post('/api/usuarios/', {'email': 'bypass@example.test', 'name': 'Bypass'})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(User.objects.count(), 1)
