from datetime import date
from importlib import import_module
from types import SimpleNamespace
from uuid import UUID, uuid4

from django.apps import apps
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Aluno, Convite, Equipe, Estoque, Item, Post, PostComment, Professor, Projeto, User


class TeamOwnerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.owner_user = User.objects.create_user(email='owner@example.com')
        self.teacher_user = User.objects.create_user(email='teacher@example.com')
        self.student_user = User.objects.create_user(email='student@example.com')
        self.owner = Professor.objects.create(
            id=UUID(int=2), user=self.owner_user, cpf='11111111111',
            telefone='47999999999', data_nascimento=date(1980, 1, 1),
        )
        self.teacher = Professor.objects.create(
            id=UUID(int=1), user=self.teacher_user, cpf='22222222222',
            telefone='47999999998', data_nascimento=date(1981, 1, 1),
        )
        self.student = Aluno.objects.create(user=self.student_user, data_nascimento=date(2005, 1, 1))
        self.team = Equipe.objects.create(nome='Robótica', criador=self.owner)
        self.team.professores.add(self.owner)
        self.team.professores.add(self.teacher)
        self.team.alunos.add(self.student)
        self.project = Projeto.objects.create(equipe=self.team, titulo='Robô', desc_curta='Robô', descricao='Robô')

    def transfer(self, professor):
        return self.client.post(
            f'/api/equipes/{self.team.pk}/transferir-owner/', {'professor': str(professor)}, format='json',
        )

    def test_transfer_gives_new_owner_exclusive_permissions(self):
        self.client.force_authenticate(self.owner_user)
        response = self.transfer(self.teacher.pk)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.data['criador']), str(self.teacher.pk))
        self.team.refresh_from_db()
        self.assertEqual(self.team.criador, self.teacher)
        self.assertTrue(self.team.professores.filter(pk=self.owner.pk).exists())
        self.assertEqual(self.transfer(self.owner.pk).status_code, 403)
        self.assertEqual(self.client.delete(f'/api/equipes/{self.team.pk}/').status_code, 403)
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.post(f'/api/equipes/{self.team.pk}/sair/').status_code, 400)
        self.client.force_authenticate(self.owner_user)
        self.assertEqual(self.client.post(f'/api/equipes/{self.team.pk}/sair/').status_code, 200)

    def test_non_owner_and_anonymous_cannot_transfer_or_delete_team(self):
        for user, expected in [(self.teacher_user, 403), (self.student_user, 403), (None, 401)]:
            with self.subTest(user=user):
                self.client.force_authenticate(user)
                self.assertEqual(self.transfer(self.teacher.pk).status_code, expected)
                self.assertEqual(self.client.delete(f'/api/equipes/{self.team.pk}/').status_code, expected)
        self.assertTrue(Equipe.objects.filter(pk=self.team.pk).exists())

    def test_invalid_transfer_does_not_change_owner(self):
        outsider_user = User.objects.create_user(email='outsider@example.com')
        outsider = Professor.objects.create(
            user=outsider_user, cpf='33333333333', telefone='47999999997', data_nascimento=date(1982, 1, 1),
        )
        self.client.force_authenticate(self.owner_user)
        for target in [self.owner.pk, outsider.pk, self.student.pk, uuid4(), 'invalid', '']:
            with self.subTest(target=target):
                self.assertEqual(self.transfer(target).status_code, 400)
        response = self.client.post(f'/api/equipes/{self.team.pk}/transferir-owner/', {}, format='json')
        self.assertEqual(response.status_code, 400)
        self.team.refresh_from_db()
        self.assertEqual(self.team.criador, self.owner)

    def test_delete_team_includes_invites_projects_posts_and_inventory(self):
        invite = Convite.objects.create(equipe=self.team, convidante=self.owner, aluno=self.student)
        stock = Estoque.objects.create(equipe=self.team)
        item = Item.objects.create(estoque=stock, nome='Motor')
        post = Post.objects.create(projeto=self.project, professor_criador=self.owner)
        comment = PostComment.objects.create(post=post, user=self.student_user, texto='Olá')
        self.client.force_authenticate(self.owner_user)
        self.assertEqual(self.client.delete(f'/api/equipes/{self.team.pk}/').status_code, 204)
        for instance in [self.team, self.project, invite, stock, item, post, comment]:
            self.assertFalse(type(instance).objects.filter(pk=instance.pk).exists())
        self.assertTrue(Professor.objects.filter(pk=self.owner.pk).exists())
        self.assertTrue(User.objects.filter(pk=self.student_user.pk).exists())

    def test_only_team_teachers_can_delete_projects_and_posts_cascade(self):
        post = Post.objects.create(projeto=self.project, professor_criador=self.owner)
        self.client.force_authenticate(self.student_user)
        self.assertEqual(self.client.delete(f'/api/projetos/{self.project.pk}/').status_code, 403)
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.delete(f'/api/projetos/{self.project.pk}/').status_code, 204)
        self.assertFalse(Post.objects.filter(pk=post.pk).exists())
        self.assertTrue(Equipe.objects.filter(pk=self.team.pk).exists())

    def test_professor_array_uses_membership_order_instead_of_uuid(self):
        response = self.client.get(f'/api/equipes/{self.team.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p['id'] for p in response.data['professores']], [str(self.owner.pk), str(self.teacher.pk)])

    def test_backfill_uses_first_membership_and_preserves_transferred_owners(self):
        legacy = Equipe.objects.create(nome='Antiga')
        legacy.professores.add(self.owner)
        legacy.professores.add(self.teacher)
        empty = Equipe.objects.create(nome='Sem professor')
        self.team.criador = self.teacher
        self.team.save(update_fields=['criador'])
        migration = import_module('core.migrations.0017_definir_owner_equipes_antigas')
        schema_editor = SimpleNamespace(connection=SimpleNamespace(alias='default'))
        migration.definir_owners(apps, schema_editor)
        migration.definir_owners(apps, schema_editor)
        legacy.refresh_from_db()
        empty.refresh_from_db()
        self.team.refresh_from_db()
        self.assertEqual(legacy.criador, self.owner)
        self.assertEqual(self.team.criador, self.teacher)
        self.assertIsNone(empty.criador)
