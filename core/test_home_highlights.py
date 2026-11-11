from datetime import date

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Equipe, Post, PostComment, PostImage, PostLike, Projeto, User
from uploader.models import Image


@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}})
class HomeHighlightsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='highlights@example.com')
        cls.voters = [User.objects.create_user(email=f'voter{i}@example.com') for i in range(5)]
        cls.teams = [Equipe.objects.create(nome=f'Equipe {i}', views=views) for i, views in enumerate([20, 80, 50, 10])]
        cls.projects = [
            Projeto.objects.create(equipe=team, titulo=f'Projeto {i}', desc_curta='Robótica', descricao='Projeto')
            for i, team in enumerate(cls.teams)
        ]
        cls.posts = [
            Post.objects.create(projeto=project, legenda=f'Post {i}') for i, project in enumerate(cls.projects)
        ]
        for post, votes in zip(cls.posts, [1, 4, 2, 0], strict=True):
            PostLike.objects.bulk_create([PostLike(post=post, user=user) for user in cls.voters[:votes]])

    def setUp(self):
        self.client.force_authenticate(self.user)

    def test_posts_are_the_global_top_three_ordered_by_likes(self):
        comments = PostComment.objects.bulk_create([
            PostComment(post=self.posts[0], user=self.user, texto=f'Comentário {i}') for i in range(6)
        ])
        response = self.client.get(reverse('posts-destaques'))

        assert response.status_code == status.HTTP_200_OK
        assert [post['id'] for post in response.data] == [self.posts[i].pk for i in [1, 2, 0]]
        assert [post['curtidas'] for post in response.data] == [4, 2, 1]
        assert response.data[0]['equipe'] == self.teams[1].nome
        assert str(response.data[0]['equipe_id']) == str(self.teams[1].pk)
        assert response.data[0]['curtiu'] is False
        assert len(response.data[2]['comentarios']) == len(comments)

    def test_new_leader_replaces_previous_highlight_after_likes_and_unlikes(self):
        post = self.posts[3]
        PostLike.objects.bulk_create([PostLike(post=post, user=user) for user in self.voters[:4]])
        self.client.post(reverse('posts-curtir', args=[post.pk]))

        response = self.client.get(reverse('posts-destaques'))
        assert response.data[0]['id'] == post.pk
        assert response.data[0]['curtidas'] == len(self.voters)
        assert response.data[0]['curtiu'] is True

        PostLike.objects.filter(post=post).delete()
        response = self.client.get(reverse('posts-destaques'))
        assert post.pk not in [item['id'] for item in response.data]

    def test_post_ties_are_resolved_by_newest_date_then_id(self):
        PostLike.objects.all().delete()
        Post.objects.update(criado_em='2026-11-11T12:00:00Z')
        response = self.client.get(reverse('posts-destaques'))
        assert [post['id'] for post in response.data] == [post.pk for post in reversed(self.posts[1:])]

    def test_images_and_missing_team_are_supported(self):
        image = Image.objects.create(file='images/highlight.jpg')
        self.teams[1].image_perfil = image
        self.teams[1].save(update_fields=['image_perfil'])
        PostImage.objects.create(post=self.posts[1], image=image)
        response = self.client.get(reverse('posts-destaques'), HTTP_HOST='localhost:8000')
        assert response.data[0]['equipe_image'].endswith('/media/images/highlight.jpg')
        assert response.data[0]['images'][0]['url'].endswith('/media/images/highlight.jpg')

        projects = self.client.get(reverse('projetos-destaques'), HTTP_HOST='localhost:8000')
        assert projects.data[0]['equipe_image'].endswith('/media/images/highlight.jpg')
        assert str(projects.data[0]['equipe_id']) == str(self.teams[1].pk)
        assert projects.data[1]['equipe_image'] is None

        self.posts[1].projeto = None
        self.posts[1].save(update_fields=['projeto'])
        response = self.client.get(reverse('posts-destaques'))
        assert response.data[0]['equipe'] is None
        assert response.data[0]['equipe_image'] is None

    def test_latest_project_per_top_team_ordered_by_team_views(self):
        newer = Projeto.objects.create(equipe=self.teams[0], titulo='Mais novo', desc_curta='Robô', descricao='Robô')
        Projeto.objects.filter(pk=self.projects[0].pk).update(data_criacao=date(2020, 1, 1))
        response = self.client.get(reverse('projetos-destaques'))

        assert response.status_code == status.HTTP_200_OK
        assert [project['id'] for project in response.data] == [self.projects[1].pk, self.projects[2].pk, newer.pk]
        assert [project['equipe_views'] for project in response.data] == [80, 50, 20]

    def test_view_changes_replace_featured_teams_and_same_day_projects_use_latest_id(self):
        newest = Projeto.objects.create(
            equipe=self.teams[3], titulo='Mais recente', desc_curta='Robô', descricao='Robô'
        )
        Equipe.objects.filter(pk=self.teams[3].pk).update(views=100)
        response = self.client.get(reverse('projetos-destaques'))

        assert [project['id'] for project in response.data] == [newest.pk, self.projects[1].pk, self.projects[2].pk]

    def test_top_team_without_projects_does_not_select_a_lower_ranked_team(self):
        self.projects[1].delete()
        response = self.client.get(reverse('projetos-destaques'))
        assert [project['id'] for project in response.data] == [self.projects[2].pk, self.projects[0].pk]

    def test_empty_highlights_and_existing_read_permissions(self):
        Post.objects.all().delete()
        Projeto.objects.all().delete()
        assert self.client.get(reverse('posts-destaques')).data == []
        assert self.client.get(reverse('projetos-destaques')).data == []
        self.client.force_authenticate(None)
        assert self.client.get(reverse('posts-destaques')).status_code == status.HTTP_401_UNAUTHORIZED
        assert self.client.get(reverse('projetos-destaques')).status_code == status.HTTP_200_OK
