# Limites e códigos HTTP explícitos são as referências destes testes de regressão.
# ruff: noqa: PLR2004
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Aluno, Convite, Equipe, Professor, User


class FormLimitsTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_limits_are_public_and_match_backend_fields(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer expired-token')
        response = self.client.get('/api/formularios/limites/')
        assert response.status_code == 200
        rules = response.data['forms']
        assert rules['item']['nome']['max_length'] == 100
        assert rules['equipe']['nome']['max_length'] == 50
        assert rules['equipe']['descricao']['max_length'] == 1000
        assert rules['projeto']['titulo']['max_length'] == 30
        assert rules['projeto']['desc_curta']['max_length'] == 60
        assert rules['projeto']['desc_curta']['required']
        assert 'max_length' not in rules['projeto']['descricao']
        assert 'min_length' not in rules['projeto']['descricao']
        assert 'max_length' not in rules['post']['legenda']
        assert rules['comentario']['texto']['max_length'] == 1000
        assert rules['usuario']['username']['max_length'] == 20
        assert rules['professor']['cpf']['max_length'] == 11
        assert rules['item']['quantidade']['min_value'] == 0
        assert int(rules['item']['quantidade']['max_value']) > 0
        assert 'verification_code_hash' not in rules['usuario']
        assert 'image/jpeg' in response.data['uploads']['image_types']


class NotificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.sender_user = User.objects.create_user(email='teacher@example.com', name='Professora Ana')
        self.recipient_user = User.objects.create_user(email='student@example.com')
        self.other_user = User.objects.create_user(email='other@example.com')
        self.teacher = Professor.objects.create(
            user=self.sender_user,
            cpf='12345678901',
            telefone='47999999999',
            data_nascimento=date(1980, 1, 1),
        )
        self.student = Aluno.objects.create(user=self.recipient_user, data_nascimento=date(2005, 1, 1))
        self.team = Equipe.objects.create(nome='Robótica', criador=self.teacher)
        self.team.professores.add(self.teacher)
        self.invite = Convite.objects.create(equipe=self.team, convidante=self.teacher, aluno=self.student)
        self.client.force_authenticate(self.recipient_user)

    def received(self):
        return self.client.get('/api/convites/recebidos/')

    def test_pending_invitation_contains_display_names(self):
        data = self.received().data
        assert len(data) == 1
        assert data[0]['equipe_nome'] == 'Robótica'
        assert data[0]['convidante_nome'] == 'Professora Ana'

    def test_accepted_invite_disappears_and_membership_is_preserved(self):
        response = self.client.post(f'/api/convites/{self.invite.pk}/aceitar/')
        assert response.status_code == 200
        assert self.received().data == []
        assert self.received().data == []
        assert self.team.alunos.filter(pk=self.student.pk).exists()
        self.invite.refresh_from_db()
        assert self.invite.status == Convite.StatusChoices.ACEITO
        assert self.client.post(f'/api/convites/{self.invite.pk}/aceitar/').status_code == 400

    def test_declined_invite_disappears_without_adding_membership(self):
        assert self.client.post(f'/api/convites/{self.invite.pk}/recusar/').status_code == 200
        assert self.received().data == []
        assert not self.team.alunos.filter(pk=self.student.pk).exists()

    def test_another_user_cannot_read_or_respond_to_invitation(self):
        self.client.force_authenticate(self.other_user)
        assert self.received().data == []
        assert self.client.post(f'/api/convites/{self.invite.pk}/aceitar/').status_code == 404
        self.invite.refresh_from_db()
        assert self.invite.status == Convite.StatusChoices.PENDENTE
