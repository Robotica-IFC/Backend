from datetime import date
from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection, transaction
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase

from core.models import Aluno, Convite, Equipe, Notificacao, Professor, User


class InviteNotificationTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sender_user = User.objects.create_user(email='sender@example.test')
        cls.student_user = User.objects.create_user(email='student@example.test')
        cls.teacher_user = User.objects.create_user(email='teacher@example.test')
        cls.other_user = User.objects.create_user(email='other@example.test')
        cls.sender = Professor.objects.create(
            user=cls.sender_user, data_nascimento=date(1980, 1, 1), telefone='47999999999',
        )
        cls.student = Aluno.objects.create(user=cls.student_user, data_nascimento=date(2000, 1, 1))
        cls.teacher = Professor.objects.create(
            user=cls.teacher_user, data_nascimento=date(1985, 1, 1), telefone='47999999998',
        )
        cls.team = Equipe.objects.create(nome='Equipe de Robótica', criador=cls.sender)
        cls.team.professores.add(cls.sender)

    def send(self, kind='aluno'):
        self.client.force_authenticate(self.sender_user)
        recipient = self.student if kind == 'aluno' else self.teacher
        return self.client.post('/api/convites/', {
            'equipe': str(self.team.pk), kind: str(recipient.pk),
        }, format='json')

    def test_invitation_notifies_only_its_recipient_without_a_project(self):
        for kind, recipient in [('aluno', self.student_user), ('professor', self.teacher_user)]:
            with self.subTest(kind=kind):
                response = self.send(kind)
                self.assertEqual(response.status_code, 201, response.data)
                notification = Notificacao.objects.get(convite_id=response.data['id'])
                self.assertEqual(notification.destinatario_id, recipient.pk)
                self.assertEqual(notification.tipo, 'CONVITE')
                self.assertIsNone(notification.projeto_id)
                self.assertIsNone(notification.lida_em)
                self.client.force_authenticate(recipient)
                listing = self.client.get('/api/notificacoes/').data
                self.assertEqual(listing['nao_lidas'], 1)
                item = listing['results'][0]
                self.assertEqual(item['convite'], response.data['id'])
                self.assertEqual(item['convite_status'], 'P')
                self.assertEqual(item['equipe'], str(self.team.pk))
                self.assertEqual(item['equipe_nome'], self.team.nome)
                self.assertIn(self.team.nome, item['mensagem'])
                unread = self.client.get('/api/notificacoes/nao-lidas/').data
                self.assertEqual(unread, {'nao_lidas': 1, 'ultima_nao_lida': notification.pk})
        self.assertFalse(self.team.alunos.filter(pk=self.student.pk).exists())
        self.assertFalse(self.team.professores.filter(pk=self.teacher.pk).exists())
        self.assertFalse(Notificacao.objects.filter(destinatario__in=[self.sender_user, self.other_user]).exists())

    def test_other_users_cannot_read_or_respond_to_the_recipient_notification(self):
        response = self.send()
        notification = Notificacao.objects.get(convite_id=response.data['id'])
        for user in [self.sender_user, self.other_user]:
            with self.subTest(user=user.pk):
                self.client.force_authenticate(user)
                self.assertEqual(self.client.get('/api/notificacoes/').data['results'], [])
                self.assertEqual(self.client.post(f'/api/notificacoes/{notification.pk}/ler/').status_code, 404)
                self.assertIn(self.client.post(f"/api/convites/{response.data['id']}/aceitar/").status_code, [403, 404])
        notification.refresh_from_db()
        self.assertIsNone(notification.lida_em)

    def test_accept_and_decline_update_notification_and_unread_counter(self):
        for kind, recipient, action, status in [
            ('aluno', self.student_user, 'aceitar', 'A'),
            ('professor', self.teacher_user, 'recusar', 'N'),
        ]:
            with self.subTest(action=action):
                invitation = self.send(kind).data
                self.client.force_authenticate(recipient)
                response = self.client.post(f"/api/convites/{invitation['id']}/{action}/")
                self.assertEqual(response.status_code, 200, response.data)
                self.assertEqual(response.data['status'], status)
                self.assertIsNotNone(response.data['notificacao_lida_em'])
                notification = Notificacao.objects.get(convite_id=invitation['id'])
                self.assertIsNotNone(notification.lida_em)
                listing = self.client.get('/api/notificacoes/').data
                self.assertEqual(listing['nao_lidas'], 0)
                self.assertEqual(listing['results'][0]['convite_status'], status)
                self.assertEqual(self.client.get('/api/notificacoes/nao-lidas/').data['nao_lidas'], 0)
                self.assertEqual(self.client.post(f"/api/convites/{invitation['id']}/{action}/").status_code, 400)
        self.assertTrue(self.team.alunos.filter(pk=self.student.pk).exists())
        self.assertFalse(self.team.professores.filter(pk=self.teacher.pk).exists())

    def test_teacher_can_accept_invite_with_nullable_recipient_relations(self):
        invite = self.send('professor').data
        self.client.force_authenticate(self.teacher_user)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.post(f"/api/convites/{invite['id']}/aceitar/")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(self.team.professores.filter(pk=self.teacher.pk).exists())
        if connection.vendor == 'postgresql':
            locking_queries = [query['sql'] for query in queries if 'FOR UPDATE' in query['sql']]
            self.assertTrue(locking_queries)
            # Consultas com DISTINCT ou JOINs opcionais não devem ser bloqueadas.
            for sql in locking_queries:
                self.assertNotIn('DISTINCT', sql.upper())
                self.assertNotIn('LEFT OUTER JOIN', sql.upper())

    def test_opening_invitation_marks_read_without_joining_and_preserves_read_date(self):
        invitation = self.send().data
        notification = Notificacao.objects.get(convite_id=invitation['id'])
        self.client.force_authenticate(self.student_user)
        read = self.client.post(f'/api/notificacoes/{notification.pk}/ler/').data['lida_em']
        self.assertFalse(self.team.alunos.filter(pk=self.student.pk).exists())
        self.assertEqual(self.client.get('/api/notificacoes/').data['results'][0]['convite_status'], 'P')
        accepted = self.client.post(f"/api/convites/{invitation['id']}/aceitar/")
        self.assertEqual(accepted.data['notificacao_lida_em'], read)

    def test_updates_and_duplicate_invites_do_not_duplicate_notification(self):
        invitation = self.send().data
        self.assertEqual(self.send().status_code, 400)
        invite = Convite.objects.get(pk=invitation['id'])
        invite.save()
        self.assertEqual(Notificacao.objects.filter(convite=invite).count(), 1)

    def test_invitation_and_notification_roll_back_together(self):
        with self.assertRaises(ValueError):
            with transaction.atomic():
                Convite.objects.create(equipe=self.team, convidante=self.sender, aluno=self.student)
                raise ValueError('Operação cancelada')
        self.assertFalse(Convite.objects.exists())
        self.assertFalse(Notificacao.objects.exists())

    def test_deleted_invitation_removes_its_notification(self):
        invitation = self.send().data
        Convite.objects.get(pk=invitation['id']).delete()
        self.assertFalse(Notificacao.objects.exists())

    def test_migration_backfills_only_pending_invitations_without_duplicates(self):
        pending, answered = Convite.objects.bulk_create([
            Convite(equipe=self.team, convidante=self.sender, aluno=self.student),
            Convite(equipe=self.team, convidante=self.sender, professor=self.teacher, status='N'),
        ])
        migration = import_module('core.migrations.0024_notificacao_convite')
        for _ in range(2):
            migration.notify_pending_invitations(apps, SimpleNamespace(connection=connection))
        self.assertEqual(Notificacao.objects.filter(convite=pending).count(), 1)
        self.assertFalse(Notificacao.objects.filter(convite=answered).exists())
        self.assertEqual(Notificacao.objects.get(convite=pending).destinatario_id, self.student_user.pk)
