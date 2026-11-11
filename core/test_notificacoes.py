from datetime import date

from django.db import transaction
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APITestCase

from core.models import Aluno, Equipe, Notificacao, Post, Professor, Projeto, User


@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}})
class NotificacaoTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.aluno_user = User.objects.create_user(email='aluno@example.com')
        cls.prof_user = User.objects.create_user(email='professor@example.com')
        cls.outro_user = User.objects.create_user(email='outro@example.com')
        cls.aluno = Aluno.objects.create(user=cls.aluno_user, data_nascimento=date(2005, 1, 1))
        cls.professor = Professor.objects.create(
            user=cls.prof_user, cpf='12345678901', telefone='47999999999', data_nascimento=date(1990, 1, 1),
        )
        cls.equipe = Equipe.objects.create(nome='Robótica')
        cls.equipe.alunos.add(cls.aluno)
        cls.equipe.professores.add(cls.professor)
        cls.projeto = Projeto.objects.create(
            titulo='Robô', desc_curta='Novo robô', descricao='Descrição', equipe=cls.equipe,
        )
        cls.list_url = reverse('notificacoes-list')

    def setUp(self):
        self.client.force_authenticate(self.aluno_user)

    def test_project_notifies_only_team_members_once_even_with_two_profiles(self):
        Aluno.objects.create(user=self.prof_user, data_nascimento=date(2000, 1, 1))
        self.equipe.alunos.add(self.prof_user.aluno_profile)
        response = self.client.post(reverse('projetos-list'), {
            'titulo': 'Segundo projeto', 'desc_curta': 'Descrição curta',
            'descricao': 'Descrição completa', 'equipe': str(self.equipe.pk),
        }, format='json')

        assert response.status_code == 201
        notifications = Notificacao.objects.filter(projeto_id=response.data['id'])
        assert notifications.count() == 2
        assert set(notifications.values_list('destinatario_id', flat=True)) == {
            self.aluno_user.pk, self.prof_user.pk,
        }
        assert set(notifications.values_list('tipo', flat=True)) == {Notificacao.Tipo.PROJETO}
        assert not notifications.filter(lida_em__isnull=False).exists()

    def test_post_creation_notifies_members_with_the_linked_project(self):
        response = self.client.post(reverse('posts-list'), {
            'legenda': 'Primeiro teste!', 'projeto': self.projeto.pk,
        }, format='json')

        assert response.status_code == 201
        notifications = Notificacao.objects.filter(tipo=Notificacao.Tipo.POST)
        assert notifications.count() == 2
        assert all(n.projeto_id == self.projeto.pk and n.post_id == response.data['id'] for n in notifications)
        assert not notifications.filter(destinatario=self.outro_user).exists()

    def test_updates_do_not_create_new_notifications(self):
        post = Post.objects.create(projeto=self.projeto, aluno_criador=self.aluno)
        before = Notificacao.objects.count()
        post.legenda = 'Editada'
        post.save()
        self.projeto.titulo = 'Título editado'
        self.projeto.save()
        assert Notificacao.objects.count() == before

    def test_post_without_project_does_not_notify(self):
        before = Notificacao.objects.count()
        Post.objects.create(aluno_criador=self.aluno, legenda='Sem projeto')
        assert Notificacao.objects.count() == before

    def test_new_members_do_not_receive_old_events(self):
        outro = Aluno.objects.create(user=self.outro_user, data_nascimento=date(2005, 1, 1))
        self.equipe.alunos.add(outro)
        assert not Notificacao.objects.filter(destinatario=self.outro_user).exists()
        Post.objects.create(projeto=self.projeto, aluno_criador=self.aluno)
        assert Notificacao.objects.filter(destinatario=self.outro_user, tipo='POST').count() == 1

    def test_inactive_and_unrelated_members_are_not_notified(self):
        self.aluno.ativo = False
        self.aluno.save()
        self.prof_user.is_active = False
        self.prof_user.save()
        post = Post.objects.create(projeto=self.projeto)
        assert not Notificacao.objects.filter(post=post).exists()

    def test_list_contains_only_own_notifications_and_global_unread_count(self):
        for _ in range(22):
            Post.objects.create(projeto=self.projeto)
        response = self.client.get(self.list_url)
        assert response.status_code == 200
        assert response.data['count'] == 23
        assert response.data['nao_lidas'] == 23
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None
        own_ids = set(Notificacao.objects.filter(destinatario=self.aluno_user).values_list('id', flat=True))
        assert all(n['id'] in own_ids for n in response.data['results'])
        assert response.data['results'][0]['id'] == max(own_ids)
        assert response.data['results'][0]['projeto'] == self.projeto.pk
        assert response.data['results'][0]['equipe_nome'] == self.equipe.nome
        page2 = self.client.get(self.list_url, {'page': 2})
        assert len(page2.data['results']) == 3

    def test_read_is_persistent_idempotent_and_independent_for_each_member(self):
        notification = Notificacao.objects.get(destinatario=self.aluno_user)
        url = reverse('notificacoes-ler', args=[notification.pk])
        first = self.client.post(url)
        second = self.client.post(url)
        assert first.status_code == 200
        assert first.data['lida_em'] is not None
        assert first.data['lida_em'] == second.data['lida_em']
        notification.refresh_from_db()
        assert notification.lida_em is not None
        assert Notificacao.objects.get(destinatario=self.prof_user).lida_em is None
        assert self.client.get(reverse('notificacoes-nao-lidas')).data['nao_lidas'] == 0
        assert self.client.get(self.list_url).data['results'][0]['lida_em'] == first.data['lida_em']
        self.client.force_authenticate(self.prof_user)
        own_list = self.client.get(self.list_url)
        assert own_list.data['results'][0]['lida_em'] is None
        assert own_list.data['nao_lidas'] == 1
        summary = self.client.get(reverse('notificacoes-nao-lidas')).data
        assert summary['ultima_nao_lida'] == Notificacao.objects.get(destinatario=self.prof_user).pk

    def test_other_users_cannot_read_or_fetch_a_notification(self):
        notification = Notificacao.objects.get(destinatario=self.prof_user)
        assert self.client.get(reverse('notificacoes-detail', args=[notification.pk])).status_code == 404
        assert self.client.post(reverse('notificacoes-ler', args=[notification.pk])).status_code == 404
        notification.refresh_from_db()
        assert notification.lida_em is None

    def test_login_required_and_clients_cannot_create_or_edit_notifications(self):
        notification = Notificacao.objects.get(destinatario=self.aluno_user)
        detail = reverse('notificacoes-detail', args=[notification.pk])
        assert self.client.post(self.list_url, {}, format='json').status_code == 405
        assert self.client.patch(detail, {'lida_em': None}, format='json').status_code == 405
        assert self.client.delete(detail).status_code == 405
        self.client.force_authenticate(None)
        assert self.client.get(self.list_url).status_code == 401
        assert self.client.get(reverse('notificacoes-nao-lidas')).status_code == 401
        assert self.client.post(reverse('notificacoes-ler', args=[notification.pk])).status_code == 401

    def test_notifications_roll_back_with_failed_creation(self):
        before = Notificacao.objects.count()
        try:
            with transaction.atomic():
                Projeto.objects.create(titulo='Rollback', equipe=self.equipe, desc_curta='Teste', descricao='Teste')
                raise ValueError('Falha na operação')
        except ValueError:
            pass
        assert Notificacao.objects.count() == before
        assert not Projeto.objects.filter(titulo='Rollback').exists()

    def test_deleted_post_keeps_project_link_and_deleted_project_removes_notifications(self):
        post = Post.objects.create(projeto=self.projeto)
        post_id = post.pk
        post.delete()
        notification = Notificacao.objects.get(destinatario=self.aluno_user, tipo='POST')
        assert notification.post_id is None
        assert notification.projeto_id == self.projeto.pk
        assert not Post.objects.filter(pk=post_id).exists()
        self.projeto.delete()
        assert not Notificacao.objects.exists()
