from datetime import date
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import (
    Aluno,
    Convite,
    Equipe,
    Estoque,
    Item,
    Post,
    PostComment,
    PostLike,
    Professor,
    Projeto,
    SugestaoProjeto,
    User,
)


class AccountDeletionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.student_user = User.objects.create_user(email='student@example.com', email_verified=True)
        self.teacher_user = User.objects.create_user(email='teacher@example.com', email_verified=True)
        self.other_user = User.objects.create_user(email='other@example.com', email_verified=True)
        self.student = Aluno.objects.create(user=self.student_user, data_nascimento=date(2005, 1, 1))
        self.teacher = self.make_teacher(self.teacher_user, '11111111111')
        self.other = self.make_teacher(self.other_user, '22222222222')
        self.team = Equipe.objects.create(nome='Robótica', criador=self.teacher)
        self.team.professores.add(self.teacher)
        self.team.alunos.add(self.student)
        self.project = Projeto.objects.create(equipe=self.team, titulo='Robô', desc_curta='Robô', descricao='Robô')

    def make_teacher(self, user, cpf):
        return Professor.objects.create(user=user, cpf=cpf, telefone='47999999999', data_nascimento=date(1980, 1, 1))

    def delete(self, user):
        self.client.force_authenticate(user)
        return self.client.delete('/api/usuarios/me/')

    def eligibility(self, user):
        self.client.force_authenticate(user)
        return self.client.get('/api/usuarios/exclusao/')

    def test_student_deletion_removes_user_profile_and_membership_but_keeps_team(self):
        assert self.eligibility(self.student_user).data['pode_excluir']
        assert self.delete(self.student_user).status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=self.student_user.pk).exists()
        assert not Aluno.objects.filter(pk=self.student.pk).exists()
        assert not self.team.alunos.exists()
        assert Equipe.objects.filter(pk=self.team.pk).exists()
        assert Projeto.objects.filter(pk=self.project.pk).exists()

    def test_teacher_without_teams_can_delete_user_and_profile(self):
        assert self.eligibility(self.other_user).data['pode_excluir']
        assert self.delete(self.other_user).status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=self.other_user.pk).exists()
        assert not Professor.objects.filter(pk=self.other.pk).exists()

    def test_only_teacher_cannot_delete_account_and_receives_team_warning(self):
        eligibility = self.eligibility(self.teacher_user)
        assert eligibility.status_code == status.HTTP_200_OK
        assert not eligibility.data['pode_excluir']
        assert 'mais de um professor responsável' in eligibility.data['detail']
        assert self.team.nome in eligibility.data['detail']
        response = self.delete(self.teacher_user)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['detail'] == eligibility.data['detail']
        assert User.objects.filter(pk=self.teacher_user.pk).exists()
        assert Professor.objects.filter(pk=self.teacher.pk).exists()
        self.team.refresh_from_db()
        assert self.team.criador == self.teacher

    def test_non_owner_teacher_can_delete_when_another_teacher_remains(self):
        self.team.professores.add(self.other)
        assert self.delete(self.other_user).status_code == status.HTTP_204_NO_CONTENT
        self.team.refresh_from_db()
        assert self.team.criador == self.teacher
        assert list(self.team.professores.all()) == [self.teacher]

    def test_owner_deletion_transfers_to_first_remaining_teacher_and_preserves_team_data(self):
        self.team.professores.add(self.other)
        third_user = User.objects.create_user(email='third@example.com')
        third = self.make_teacher(third_user, '33333333333')
        self.team.professores.add(third)
        stock = Estoque.objects.create(equipe=self.team)
        item = Item.objects.create(estoque=stock, nome='Motor')
        assert self.eligibility(self.teacher_user).data['pode_excluir']
        assert self.delete(self.teacher_user).status_code == status.HTTP_204_NO_CONTENT
        self.team.refresh_from_db()
        assert self.team.criador == self.other
        assert not Professor.objects.filter(pk=self.teacher.pk).exists()
        assert not User.objects.filter(pk=self.teacher_user.pk).exists()
        for instance in [self.team, self.project, stock, item, self.other, third, self.student]:
            assert type(instance).objects.filter(pk=instance.pk).exists()

    def test_every_team_is_checked_before_any_changes(self):
        self.team.professores.add(self.other)
        solo = Equipe.objects.create(nome='Equipe solo', criador=self.teacher, ativo=False)
        solo.professores.add(self.teacher)
        invitation = Convite.objects.create(convidante=self.teacher, equipe=self.team, aluno=self.student)
        post = Post.objects.create(projeto=self.project, professor_criador=self.teacher)
        response = self.delete(self.teacher_user)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert solo.nome in response.data['detail']
        assert self.team.nome not in response.data['detail']
        self.team.refresh_from_db()
        assert self.team.criador == self.teacher
        for instance in [self.teacher_user, self.teacher, invitation, post]:
            assert type(instance).objects.filter(pk=instance.pk).exists()

    def test_legacy_owner_without_membership_still_requires_a_successor(self):
        self.team.professores.clear()
        assert self.delete(self.teacher_user).status_code == status.HTTP_400_BAD_REQUEST
        self.team.professores.add(self.other)
        assert self.delete(self.teacher_user).status_code == status.HTTP_204_NO_CONTENT
        self.team.refresh_from_db()
        assert self.team.criador == self.other

    def test_cleanup_includes_authored_posts_invites_and_interactions(self):
        self.team.professores.add(self.other)
        own_post = Post.objects.create(projeto=self.project, professor_criador=self.teacher)
        own_post_comment = PostComment.objects.create(post=own_post, user=self.student_user, texto='Olá')
        other_post = Post.objects.create(projeto=self.project, aluno_criador=self.student)
        like = PostLike.objects.create(post=other_post, user=self.teacher_user)
        comment = PostComment.objects.create(post=other_post, user=self.teacher_user, texto='Olá')
        sent = Convite.objects.create(equipe=self.team, convidante=self.teacher, aluno=self.student)
        received = Convite.objects.create(equipe=self.team, convidante=self.other, professor=self.teacher)
        untouched = Convite.objects.create(equipe=self.team, convidante=self.other, aluno=self.student)
        suggestion = SugestaoProjeto.objects.create(
            equipe=self.team, autor=self.teacher_user, titulo='Ideia', descricao='Robô'
        )
        assert self.delete(self.teacher_user).status_code == status.HTTP_204_NO_CONTENT
        for instance in [own_post, own_post_comment, like, comment, sent, received]:
            assert not type(instance).objects.filter(pk=instance.pk).exists()
        assert Post.objects.filter(pk=other_post.pk).exists()
        assert Convite.objects.filter(pk=untouched.pk).exists()
        suggestion.refresh_from_db()
        assert suggestion.autor is None

    def test_student_posts_and_invitations_do_not_prevent_permanent_deletion(self):
        post = Post.objects.create(projeto=self.project, aluno_criador=self.student)
        invitation = Convite.objects.create(equipe=self.team, convidante=self.teacher, aluno=self.student)
        assert self.delete(self.student_user).status_code == status.HTTP_204_NO_CONTENT
        assert not Post.objects.filter(pk=post.pk).exists()
        assert not Convite.objects.filter(pk=invitation.pk).exists()
        assert User.objects.filter(pk=self.teacher_user.pk).exists()

    def test_delete_failure_rolls_back_transfer_and_cleanup(self):
        self.team.professores.add(self.other)
        post = Post.objects.create(projeto=self.project, professor_criador=self.teacher)
        invitation = Convite.objects.create(equipe=self.team, convidante=self.teacher, aluno=self.student)
        with patch.object(User, 'delete', side_effect=IntegrityError('Deletion failed')):
            with self.assertRaises(IntegrityError):  # noqa: PT027 - Django TestCase
                self.delete(self.teacher_user)
        self.team.refresh_from_db()
        assert self.team.criador == self.teacher
        for instance in [post, invitation, self.teacher_user, self.teacher]:
            assert type(instance).objects.filter(pk=instance.pk).exists()

    def test_anonymous_cannot_check_or_delete_accounts_through_any_route(self):
        self.client.force_authenticate(None)
        assert self.client.get('/api/usuarios/exclusao/').status_code == status.HTTP_401_UNAUTHORIZED
        for url in [
            '/api/usuarios/me/',
            f'/api/usuarios/{self.student_user.pk}/',
            f'/api/alunos/{self.student.pk}/',
            f'/api/professores/{self.teacher.pk}/',
        ]:
            with self.subTest(url=url):
                assert self.client.delete(url).status_code == status.HTTP_401_UNAUTHORIZED
        assert User.objects.filter(pk=self.student_user.pk).exists()

    def test_other_users_cannot_delete_someone_elses_account_or_profile(self):
        self.client.force_authenticate(self.other_user)
        for url in [
            f'/api/usuarios/{self.student_user.pk}/',
            f'/api/alunos/{self.student.pk}/',
            f'/api/professores/{self.teacher.pk}/',
        ]:
            with self.subTest(url=url):
                assert self.client.delete(url).status_code == status.HTTP_403_FORBIDDEN
        assert User.objects.filter(pk=self.student_user.pk).exists()
        assert Professor.objects.filter(pk=self.teacher.pk).exists()

    def test_profile_delete_routes_also_remove_user_and_enforce_teacher_rule(self):
        self.client.force_authenticate(self.student_user)
        assert self.client.delete(f'/api/alunos/{self.student.pk}/').status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=self.student_user.pk).exists()
        self.client.force_authenticate(self.teacher_user)
        assert self.client.delete(f'/api/professores/{self.teacher.pk}/').status_code == status.HTTP_400_BAD_REQUEST
        self.team.professores.add(self.other)
        assert self.client.delete(f'/api/professores/{self.teacher.pk}/').status_code == status.HTTP_204_NO_CONTENT
        assert not User.objects.filter(pk=self.teacher_user.pk).exists()

    def test_user_detail_delete_cannot_bypass_team_rule(self):
        self.client.force_authenticate(self.teacher_user)
        url = f'/api/usuarios/{self.teacher_user.pk}/'
        assert self.client.delete(url).status_code == status.HTTP_400_BAD_REQUEST
        self.team.professores.add(self.other)
        assert self.client.delete(url).status_code == status.HTTP_204_NO_CONTENT
        assert not Professor.objects.filter(pk=self.teacher.pk).exists()

    def test_deleted_account_access_and_refresh_tokens_stop_working(self):
        refresh = RefreshToken.for_user(self.student_user)
        access = str(refresh.access_token)
        assert self.delete(self.student_user).status_code == status.HTTP_204_NO_CONTENT
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        assert self.client.get('/api/usuarios/me/').status_code == status.HTTP_401_UNAUTHORIZED
        self.client.credentials()
        assert (
            self.client.post('/api/token/refresh/', {'refresh': str(refresh)}).status_code
            == status.HTTP_401_UNAUTHORIZED
        )

    def test_existing_account_can_still_refresh_its_token(self):
        refresh = RefreshToken.for_user(self.student_user)
        response = self.client.post('/api/token/refresh/', {'refresh': str(refresh)})
        assert response.status_code == status.HTTP_200_OK
        assert response.data['access']
