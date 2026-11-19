from rest_framework.test import APITestCase

from core.models import Categoria, Equipe, Instituicao, Projeto


class ResourceFilterTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.institution = Instituicao.objects.create(nome='IFC Araquari', cidade='Araquari', estado='SC')
        cls.category = Categoria.objects.create(nome='Automação')
        cls.team = Equipe.objects.create(nome='Cypher', instituicao=cls.institution)
        cls.team.categorias.add(cls.category)
        cls.other = Equipe.objects.create(nome='Viper', ativo=False)
        cls.project = Projeto.objects.create(
            equipe=cls.team,
            titulo='Robô seguidor',
            desc_curta='Sensores de linha',
            descricao='Automação',
        )
        Projeto.objects.create(equipe=cls.other, titulo='Resgate', status='CONCLUIDO')

    def test_project_search_combines_with_relations_status_and_pagination(self):
        response = self.client.get(
            '/api/projetos/',
            {
                'search': 'SENSORES',
                'equipe': self.team.pk,
                'equipe__instituicao': self.institution.pk,
                'status': 'EM_ANDAMENTO',
                'page_size': 1,
            },
        )
        assert response.status_code == 200
        assert [item['id'] for item in response.data['results']] == [self.project.pk]
        assert response.data['total_pages'] == 1
        empty = self.client.get('/api/projetos/', {'search': 'Sensores', 'status': 'CONCLUIDO'})
        assert empty.data['results'] == []

    def test_invalid_project_filter_returns_validation_error(self):
        for params in ({'status': 'invalid'}, {'equipe': 'invalid'}):
            assert self.client.get('/api/projetos/', params).status_code == 400

    def test_team_search_combines_with_category_institution_and_active(self):
        response = self.client.get(
            '/api/equipes/',
            {
                'search': 'CYP',
                'categorias': self.category.pk,
                'instituicao__nome': self.institution.nome,
                'ativo': 'true',
            },
        )
        assert response.status_code == 200
        assert [str(item['id']) for item in response.data['items']] == [str(self.team.pk)]
        inactive = self.client.get('/api/equipes/', {'ativo': 'false'})
        assert [str(item['id']) for item in inactive.data['items']] == [str(self.other.pk)]

    def test_filter_options_are_public_and_not_limited_to_current_page(self):
        for resource in ('projetos', 'equipes'):
            response = self.client.get(f'/api/{resource}/filtros/')
            assert response.status_code == 200
            assert len(response.data['equipes']) == 2
            assert response.data['categorias'][0]['nome'] == self.category.nome
            assert str(response.data['instituicoes'][0]['id']) == str(self.institution.pk)
