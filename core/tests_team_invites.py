from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import User, Aluno, Professor, Equipe, Convite


class ConvitesEquipeTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner_user = User.objects.create_user(email='owner@test.example')
        self.teacher_user = User.objects.create_user(email='teacher@test.example')
        self.student_user = User.objects.create_user(email='student@test.example')
        self.other_user = User.objects.create_user(email='other@test.example')
        self.owner = Professor.objects.create(user=self.owner_user, cpf='11111111111', telefone='47999999999', data_nascimento=date(1985, 1, 1))
        self.teacher = Professor.objects.create(user=self.teacher_user, cpf='22222222222', telefone='47999999998', data_nascimento=date(1986, 1, 1))
        self.student = Aluno.objects.create(user=self.student_user, data_nascimento=date(2006, 1, 1))
        self.other = Aluno.objects.create(user=self.other_user, data_nascimento=date(2006, 2, 2))
        self.team = Equipe.objects.create(nome='Robótica', criador=self.owner)
        self.team.professores.add(self.owner, self.teacher)
        self.team.alunos.add(self.student)

    def test_non_creator_cannot_remove_student(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.delete(f'/api/equipes/{self.team.pk}/membros/{self.student.pk}/?tipo=aluno')
        self.assertEqual(response.status_code, 403)

    def test_creator_cannot_be_removed(self):
        self.client.force_authenticate(self.owner_user)
        response = self.client.delete(f'/api/equipes/{self.team.pk}/membros/{self.owner.pk}/?tipo=professor')
        self.assertEqual(response.status_code, 400)

    def test_invitation_acceptance_adds_student(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.post('/api/convites/', {'equipe': str(self.team.pk), 'aluno': str(self.other.pk)}, format='json')
        self.assertEqual(response.status_code, 201)
        invitation_id = response.data['id']
        self.assertFalse(self.team.alunos.filter(pk=self.other.pk).exists())
        self.client.force_authenticate(self.other_user)
        response = self.client.post(f'/api/convites/{invitation_id}/aceitar/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.team.alunos.filter(pk=self.other.pk).exists())

    def test_unrelated_user_cannot_accept_invitation(self):
        self.client.force_authenticate(self.owner_user)
        response = self.client.post('/api/convites/', {'equipe': str(self.team.pk), 'aluno': str(self.other.pk)}, format='json')
        self.client.force_authenticate(self.student_user)
        self.assertEqual(self.client.post(f"/api/convites/{response.data['id']}/aceitar/").status_code, 403)
