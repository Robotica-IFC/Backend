import re

from django.core import mail
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Professor


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ProfessorRegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def register(self, username, **extra):
        return self.client.post('/api/professores/', {
            'name': 'Professor',
            'username': username,
            'email': f'{username}@example.com',
            'password': 'StrongPass123!',
            'telefone': '47999999999',
            'data_nascimento': '1980-01-01',
            **extra,
        }, format='json')

    def complete(self, response):
        assert response.status_code == status.HTTP_202_ACCEPTED, response.data
        code = re.search(r'\b[0-9]{6}\b', mail.outbox[-1].body).group()
        verified = self.client.post('/api/verificar-email/', {
            'email': response.data['email'], 'registration_token': response.data['registration_token'], 'codigo': code,
        })
        assert verified.status_code == status.HTTP_200_OK, verified.data
        return Professor.objects.get(user__email=response.data['email'])

    def test_multiple_registrations_accept_missing_empty_or_null_cpf(self):
        cases = [{}, {}, {'cpf': ''}, {'cpf': ''}, {'cpf': None}, {'cpf': '   '}]
        for index, extra in enumerate(cases):
            with self.subTest(extra=extra, index=index):
                response = self.register(f'prof{index}', **extra)
                professor = self.complete(response)
                assert professor.cpf is None

    def test_provided_cpf_is_preserved_and_remains_unique(self):
        response = self.register('prof1', cpf='12345678901')
        assert self.complete(response).cpf == '12345678901'
        duplicate = self.register('prof2', cpf='12345678901')
        assert duplicate.status_code == status.HTTP_400_BAD_REQUEST, duplicate.data
        assert 'cpf' in duplicate.data

    def test_existing_cpf_can_be_cleared(self):
        created = self.register('prof1', cpf='12345678901')
        professor = self.complete(created)
        response = self.client.patch(f'/api/professores/{professor.pk}/', {'cpf': ''}, format='json')
        assert response.status_code == status.HTTP_200_OK, response.data
        assert Professor.objects.get(pk=professor.pk).cpf is None

    def test_provided_cpf_still_respects_max_length(self):
        response = self.register('prof1', cpf='123456789012')
        assert response.status_code == status.HTTP_400_BAD_REQUEST, response.data
        assert 'cpf' in response.data
