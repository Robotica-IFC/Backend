from unittest.mock import patch

from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from core.models import Aluno, Professor, User
from core.serializers import AlunoSerializer, ProfessorSerializer


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationEmailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='existente@example.com', password='OriginalPass123!', email_verified=True,
        )

    def payload(self, email):
        return {
            'email': email, 'name': 'Novo cadastro', 'username': 'novo',
            'password': 'DifferentPass456!', 'data_nascimento': '2000-01-01',
            'telefone': '47999999999',
        }

    def assert_duplicate(self, response):
        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn('Já existe uma conta com este e-mail', response.data['email'][0])
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Aluno.objects.count(), 0)
        self.assertEqual(Professor.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('OriginalPass123!'))

    def test_existing_email_is_rejected_for_both_profiles_and_letter_cases(self):
        for route in ['alunos', 'professores']:
            for email in [self.user.email, 'EXISTENTE@EXAMPLE.COM', '  existente@example.com  ']:
                with self.subTest(route=route, email=email):
                    response = self.client.post(f'/api/{route}/', self.payload(email))
                    self.assert_duplicate(response)

    def test_pending_account_is_also_reported_as_existing(self):
        User.objects.filter(pk=self.user.pk).update(email_verified=False)
        for route in ['alunos', 'professores']:
            with self.subTest(route=route):
                self.assert_duplicate(self.client.post(f'/api/{route}/', self.payload(self.user.email)))

    def test_conflict_after_validation_returns_warning_without_server_error(self):
        for serializer_class in [AlunoSerializer, ProfessorSerializer]:
            with self.subTest(serializer=serializer_class.__name__):
                serializer = serializer_class(data=self.payload(self.user.email))
                with patch.object(serializer_class, 'validate_email', return_value=self.user.email):
                    self.assertTrue(serializer.is_valid(), serializer.errors)
                with self.assertRaises(ValidationError) as raised:
                    serializer.save()
                self.assertIn('Já existe uma conta', raised.exception.detail['email'][0])
                self.assertEqual(User.objects.count(), 1)
