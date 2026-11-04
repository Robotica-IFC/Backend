from datetime import date
from django.test import TestCase
from rest_framework.test import APIClient
from core.models import User, Professor, Aluno, Equipe, Projeto, Post, PostLike, PostComment


class PostSocialTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.teacher_user = User.objects.create_user(email='teacher@test.example', password='TestPass123!')
        self.other_user = User.objects.create_user(email='other@test.example', password='TestPass123!')
        self.student_user = User.objects.create_user(email='student@test.example', password='TestPass123!')
        self.teacher = Professor.objects.create(user=self.teacher_user, cpf='12345678901', telefone='47999999999', data_nascimento=date(1980, 1, 1))
        self.student = Aluno.objects.create(user=self.student_user, data_nascimento=date(2005, 1, 1))
        self.team = Equipe.objects.create(nome='Robótica')
        self.team.professores.add(self.teacher)
        self.team.alunos.add(self.student)
        self.project = Projeto.objects.create(equipe=self.team, titulo='Robô', descricao='Um robô', desc_curta='Robô')
        self.post = Post.objects.create(projeto=self.project, professor_criador=self.teacher, legenda='Texto original')

    def test_only_teacher_can_edit_team_and_project(self):
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.patch(f'/api/equipes/{self.team.pk}/', {'nome': 'Alterada'}).status_code, 403)
        self.assertEqual(self.client.patch(f'/api/projetos/{self.project.pk}/', {'titulo': 'Alterado'}).status_code, 403)
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.patch(f'/api/equipes/{self.team.pk}/', {'nome': 'Alterada'}).status_code, 200)
        self.assertEqual(self.client.patch(f'/api/projetos/{self.project.pk}/', {'titulo': 'Alterado'}).status_code, 200)

    def test_only_author_can_edit_post(self):
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.patch(f'/api/posts/{self.post.pk}/', {'legenda': 'Outro'}).status_code, 403)
        self.client.force_authenticate(self.teacher_user)
        self.assertEqual(self.client.patch(f'/api/posts/{self.post.pk}/', {'legenda': 'Atualizado'}).status_code, 200)

    def test_like_is_idempotent(self):
        self.client.force_authenticate(self.student_user)
        url = f'/api/posts/{self.post.pk}/curtir/'
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(self.client.post(url).status_code, 200)
        self.assertEqual(PostLike.objects.filter(post=self.post).count(), 1)
        self.assertEqual(self.client.delete(url).status_code, 200)
        self.assertFalse(PostLike.objects.filter(post=self.post).exists())

    def test_comment_authorization_and_validation(self):
        url = f'/api/posts/{self.post.pk}/comentarios/'
        self.client.force_authenticate(self.student_user)
        self.assertEqual(self.client.post(url, {'texto': ' '}).status_code, 400)
        r = self.client.post(url, {'texto': 'Parabéns!'})
        self.assertEqual(r.status_code, 201)
        comment = PostComment.objects.get(pk=r.data['id'])
        self.client.force_authenticate(self.other_user)
        self.assertEqual(self.client.delete(f'{url}{comment.pk}/').status_code, 403)
        self.client.force_authenticate(self.student_user)
        self.assertEqual(self.client.delete(f'{url}{comment.pk}/').status_code, 204)

    def test_post_image_format_defaults_to_rectangle(self):
        self.assertEqual(self.post.formato_imagem, 'RETANGULAR')
        self.client.force_authenticate(self.teacher_user)
        response = self.client.get(f'/api/posts/{self.post.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['formato_imagem'], 'RETANGULAR')

    def test_post_author_can_change_image_format(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.patch(
            f'/api/posts/{self.post.pk}/',
            {'formato_imagem': 'QUADRADO'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.formato_imagem, 'QUADRADO')

    def test_post_rejects_invalid_image_format(self):
        self.client.force_authenticate(self.teacher_user)
        response = self.client.patch(
            f'/api/posts/{self.post.pk}/',
            {'formato_imagem': 'VERTICAL'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)
        self.post.refresh_from_db()
        self.assertEqual(self.post.formato_imagem, 'RETANGULAR')
