from datetime import date
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Aluno, Equipe, Estoque, Instituicao, Professor, Projeto, SugestaoProjeto, User
from core.serializers import EquipeListRetrieveSerializer, EstoqueSerializer
from uploader.models import Image


class EstoqueSerializerTests(TestCase):
    def test_duplicate_equipe_stock_is_rejected(self):
        equipe = Equipe.objects.create(nome='Equipe Alpha')
        Estoque.objects.create(equipe=equipe)

        serializer = EstoqueSerializer(data={'equipe': str(equipe.id)})

        assert not serializer.is_valid()
        assert 'equipe' in serializer.errors

    def test_equipe_retrieve_includes_estoque_id(self):
        equipe = Equipe.objects.create(nome='Equipe Beta')
        estoque = Estoque.objects.create(equipe=equipe)

        serializer = EquipeListRetrieveSerializer(equipe)

        assert serializer.data['estoque_id'] == estoque.id


class ProjetoOrigemAPITests(APITestCase):
    def test_creation_list_and_detail_preserve_suggestion_origin(self):
        equipe = Equipe.objects.create(nome='Equipe Alpha')
        self.client.force_authenticate(User.objects.create_user(email='professor@example.com'))
        for from_suggestion in [True, False]:
            with self.subTest(from_suggestion=from_suggestion):
                created = self.client.post(reverse('projetos-list'), {
                    'titulo': 'Robô reciclador', 'desc_curta': 'Coleta seletiva',
                    'descricao': 'Projeto de coleta seletiva.', 'equipe': str(equipe.pk),
                    'sugestao': from_suggestion,
                }, format='json')

                assert created.status_code == status.HTTP_201_CREATED
                detail = self.client.get(reverse('projetos-detail', args=[created.data['id']]))
                listing = self.client.get(reverse('projetos-list'), {'equipe': str(equipe.pk)})
                project = next(item for item in listing.data['results'] if item['id'] == created.data['id'])
                assert detail.data['sugestao'] is from_suggestion
                assert project['sugestao'] is from_suggestion


@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}})
class EquipeOpcoesAPITests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.imagem = Image.objects.create(file='images/cypher.png')
        cls.equipe = Equipe.objects.create(nome='Equipe Cypher', image_perfil=cls.imagem, views=10)
        cls.sem_imagem = Equipe.objects.create(nome='Equipe Alpha', views=8)
        cls.inativa = Equipe.objects.create(nome='Cypher inativa', ativo=False, views=5)
        cls.equipes = [cls.equipe, cls.sem_imagem, cls.inativa]
        cls.url = reverse('equipes-opcoes')

    def test_options_return_only_requested_fields(self):
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == len(self.equipes)
        assert all(set(item) == {'id', 'nome', 'image_perfil'} for item in response.data['items'])
        item = response.data['items'][0]
        assert item['id'] == str(self.equipe.pk)
        assert item['nome'] == self.equipe.nome
        assert item['image_perfil'] == {
            'attachment_key': str(self.imagem.attachment_key),
            'url': self.imagem.url,
        }

    def test_options_support_teams_without_image(self):
        response = self.client.get(self.url, {'search': 'Alpha'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['items'] == [
            {'id': str(self.sem_imagem.pk), 'nome': self.sem_imagem.nome, 'image_perfil': None}
        ]

    def test_options_combine_partial_name_search_with_active_filter(self):
        response = self.client.get(self.url, {'search': 'YPH', 'ativo': 'true'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 1
        assert [item['id'] for item in response.data['items']] == [str(self.equipe.pk)]

    def test_options_return_empty_items_when_search_does_not_match(self):
        response = self.client.get(self.url, {'search': 'inexistente'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == 0
        assert response.data['items'] == []

    def test_options_preserve_team_pagination(self):
        pagina = 2
        response = self.client.get(self.url, {'page_size': 1, 'page': pagina})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total'] == len(self.equipes)
        assert response.data['paginas'] == len(self.equipes)
        assert response.data['pagina_atual'] == pagina
        assert [item['id'] for item in response.data['items']] == [str(self.sem_imagem.pk)]

    def test_standard_team_list_keeps_its_existing_fields(self):
        response = self.client.get(reverse('equipes-list'))

        assert response.status_code == status.HTTP_200_OK
        assert 'descricao' in response.data['items'][0]
        assert 'professores' in response.data['items'][0]
        assert 'instituicao' in response.data['items'][0]


@override_settings(STORAGES={'default': {'BACKEND': 'django.core.files.storage.InMemoryStorage'}})
class SugestaoProjetoAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.instituicao = Instituicao.objects.create(nome='IFC Araquari', cidade='Araquari', estado='SC')
        cls.outra_instituicao = Instituicao.objects.create(nome='IFC Brusque', cidade='Brusque', estado='SC')
        cls.equipe = Equipe.objects.create(nome='Cypher', instituicao=cls.instituicao)
        cls.outra_equipe = Equipe.objects.create(nome='Outra equipe', instituicao=cls.outra_instituicao)
        cls.equipe_inativa = Equipe.objects.create(nome='Inativa', instituicao=cls.instituicao, ativo=False)
        cls.autor = User.objects.create_user(email='autor@example.com', name='Autor')
        cls.outro_usuario = User.objects.create_user(email='outro@example.com')
        cls.admin = User.objects.create_user(email='admin@example.com', is_staff=True)
        cls.aluno_user = User.objects.create_user(email='aluno@example.com')
        cls.professor_user = User.objects.create_user(email='professor@example.com')
        aluno = Aluno.objects.create(user=cls.aluno_user, data_nascimento=date(2005, 1, 1))
        professor = Professor.objects.create(
            user=cls.professor_user,
            cpf='12345678901',
            telefone='47999999999',
            data_nascimento=date(1990, 1, 1),
            instituicao=cls.instituicao,
        )
        cls.equipe.alunos.add(aluno)
        cls.equipe.professores.add(professor)
        cls.url = reverse('sugestoes-projetos-list')

    def setUp(self):
        self.client.force_authenticate(self.autor)
        self.payload = {
            'titulo': 'Robô de coleta seletiva',
            'equipe': str(self.equipe.pk),
            'descricao': 'Construir um robô para separar materiais recicláveis.',
            'anonimo': True,
        }


class SugestaoProjetoEnvioAPITests(SugestaoProjetoAPITestCase):
    def test_authenticated_anonymous_submission_does_not_create_a_project(self):
        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        sugestao = SugestaoProjeto.objects.get(pk=response.data['id'])
        assert sugestao.titulo == self.payload['titulo']
        assert sugestao.descricao == self.payload['descricao']
        assert sugestao.equipe == self.equipe
        assert 'instituicao' not in response.data
        assert sugestao.anonimo
        assert sugestao.autor is None
        assert sugestao.criado_em is not None
        assert not sugestao.anexos.exists()
        assert not Projeto.objects.exists()

    def test_submission_defaults_to_anonymous(self):
        self.payload.pop('anonimo')

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['anonimo']
        assert response.data['autor'] is None

    def test_identified_submission_uses_the_authenticated_user(self):
        self.client.force_authenticate(user=None)
        token = AccessToken.for_user(self.autor)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        self.payload.update(anonimo=False, autor=self.outro_usuario.pk)

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        sugestao = SugestaoProjeto.objects.get(pk=response.data['id'])
        assert sugestao.autor == self.autor
        assert not sugestao.anonimo

    def test_authenticated_user_can_send_anonymously_without_saving_identity(self):
        self.client.force_authenticate(self.autor)
        self.payload['autor'] = self.autor.pk

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert SugestaoProjeto.objects.get(pk=response.data['id']).autor is None
        assert response.data['autor'] is None

    def test_all_submissions_require_authentication(self):
        self.client.force_authenticate(user=None)
        for anonimo in [True, False]:
            with self.subTest(anonimo=anonimo):
                response = self.client.post(self.url, {**self.payload, 'anonimo': anonimo}, format='json')

                assert response.status_code == status.HTTP_401_UNAUTHORIZED
        self.payload.pop('anonimo')
        response = self.client.post(self.url, self.payload, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert not SugestaoProjeto.objects.exists()

    def test_required_fields_are_validated(self):
        for field in ['titulo', 'equipe', 'descricao']:
            with self.subTest(field=field):
                payload = self.payload.copy()
                payload.pop(field)

                response = self.client.post(self.url, payload, format='json')

                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert field in response.data
        assert not SugestaoProjeto.objects.exists()

    def test_empty_text_is_rejected(self):
        for field in ['titulo', 'descricao']:
            with self.subTest(field=field):
                response = self.client.post(self.url, {**self.payload, field: '   '}, format='json')

                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert field in response.data
        assert not SugestaoProjeto.objects.exists()

    def test_description_and_title_length_limits_are_enforced(self):
        for field, length in [('descricao', 1000), ('titulo', 30)]:
            with self.subTest(field=field):
                response = self.client.post(self.url, {**self.payload, field: 'a' * (length + 1)}, format='json')

                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert field in response.data
        assert not SugestaoProjeto.objects.exists()

    def test_description_and_title_accept_their_maximum_lengths(self):
        self.payload.update(titulo='a' * 30, descricao='a' * 1000)

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED

    def test_submission_can_target_a_team_from_any_institution(self):
        self.payload['equipe'] = str(self.outra_equipe.pk)

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert SugestaoProjeto.objects.get(pk=response.data['id']).equipe == self.outra_equipe

    def test_submission_can_target_a_team_without_institution(self):
        equipe = Equipe.objects.create(nome='Equipe independente')
        self.payload['equipe'] = str(equipe.pk)

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert SugestaoProjeto.objects.get(pk=response.data['id']).equipe == equipe

    def test_inactive_team_is_rejected(self):
        self.payload['equipe'] = str(self.equipe_inativa.pk)

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'equipe' in response.data

    def test_unknown_or_invalid_relations_are_rejected(self):
        for value in [str(uuid4()), 'invalido']:
            with self.subTest(value=value):
                response = self.client.post(self.url, {**self.payload, 'equipe': value}, format='json')

                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert 'equipe' in response.data
        assert not SugestaoProjeto.objects.exists()

    def test_authenticated_submission_supports_multiple_uploaded_documents(self):
        attachment_keys = []
        for name in ['proposta.pdf', 'referencia.pdf']:
            document = SimpleUploadedFile(name, b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF', 'application/pdf')
            upload = self.client.post('/api/media/documents/', {'file': document}, format='multipart')
            assert upload.status_code == status.HTTP_201_CREATED
            attachment_keys.append(upload.data['attachment_key'])
        self.payload['anexos'] = attachment_keys

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        sugestao = SugestaoProjeto.objects.get(pk=response.data['id'])
        assert sugestao.anexos.count() == len(attachment_keys)
        self.client.force_authenticate(self.professor_user)
        detail = self.client.get(
            reverse('sugestoes-projetos-detail', args=[sugestao.pk]), HTTP_HOST='backend.example:8000',
        )
        assert detail.status_code == status.HTTP_200_OK
        assert len(detail.data['anexos']) == len(attachment_keys)
        assert all(anexo['url'].startswith('http://backend.example:8000/media/') for anexo in detail.data['anexos'])

    def test_unknown_attachment_does_not_save_the_suggestion(self):
        self.payload['anexos'] = [str(uuid4())]

        response = self.client.post(self.url, self.payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'anexos' in response.data
        assert not SugestaoProjeto.objects.exists()


class SugestaoProjetoEstadoAPITests(SugestaoProjetoAPITestCase):
    actions = ['favoritar', 'desfavoritar', 'recusar', 'aceitar']

    def setUp(self):
        super().setUp()
        self.payload['anonimo'] = False
        created = self.client.post(self.url, self.payload, format='json')
        self.sugestao = SugestaoProjeto.objects.get(pk=created.data['id'])
        self.client.force_authenticate(self.professor_user)

    def perform_action(self, action):
        return self.client.post(
            reverse(f'sugestoes-projetos-{action}', args=[self.sugestao.pk]), format='json',
        )

    def test_favorite_and_unfavorite_persist_and_return_complete_suggestion(self):
        for action, expected in [('favoritar', True), ('favoritar', True), ('desfavoritar', False)]:
            with self.subTest(action=action):
                response = self.perform_action(action)

                assert response.status_code == status.HTTP_200_OK
                assert response.data['favorita'] is expected
                assert response.data['titulo'] == self.payload['titulo']
                assert response.data['autor']['id'] == self.autor.pk
                assert response.data['anexos'] == []
                self.sugestao.refresh_from_db()
                assert self.sugestao.favorita is expected

    def test_reject_and_restore_persist_and_keep_favorite(self):
        self.perform_action('favoritar')
        rejected = self.perform_action('recusar')

        assert rejected.status_code == status.HTTP_200_OK
        assert rejected.data['recusada'] is True
        assert rejected.data['recusada_em'] is not None
        self.sugestao.refresh_from_db()
        assert self.sugestao.recusada
        assert self.sugestao.recusada_em is not None
        assert self.sugestao.favorita

        repeated = self.perform_action('recusar')
        assert repeated.data['recusada_em'] == rejected.data['recusada_em']

        restored = self.perform_action('aceitar')
        assert restored.status_code == status.HTTP_200_OK
        assert restored.data['recusada'] is False
        assert restored.data['recusada_em'] is None
        assert restored.data['favorita'] is True
        self.sugestao.refresh_from_db()
        assert not self.sugestao.recusada
        assert self.sugestao.recusada_em is None
        assert not Projeto.objects.exists()

    def test_list_and_detail_include_saved_state(self):
        self.perform_action('favoritar')
        rejected = self.perform_action('recusar')

        listing = self.client.get(self.url, {'equipe': str(self.equipe.pk)})
        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[self.sugestao.pk]))

        for data in [listing.data['results'][0], detail.data]:
            assert data['favorita'] is True
            assert data['recusada'] is True
            assert data['recusada_em'] == rejected.data['recusada_em']

    def test_author_and_team_student_cannot_manage_suggestions(self):
        for user in [self.autor, self.aluno_user]:
            self.client.force_authenticate(user)
            for action in self.actions:
                with self.subTest(user=user.pk, action=action):
                    response = self.perform_action(action)
                    assert response.status_code == status.HTTP_403_FORBIDDEN
        self.sugestao.refresh_from_db()
        assert not self.sugestao.favorita
        assert not self.sugestao.recusada
        assert self.sugestao.recusada_em is None

    def test_unrelated_users_and_teachers_cannot_manage_other_teams(self):
        self.sugestao.equipe = self.outra_equipe
        self.sugestao.save(update_fields=['equipe'])

        for user in [self.outro_usuario, self.professor_user]:
            self.client.force_authenticate(user)
            for action in self.actions:
                with self.subTest(user=user.pk, action=action):
                    response = self.perform_action(action)
                    assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_public_cannot_manage_suggestions(self):
        self.client.force_authenticate(user=None)

        for action in self.actions:
            with self.subTest(action=action):
                response = self.perform_action(action)
                assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_staff_can_manage_suggestions(self):
        self.client.force_authenticate(self.admin)

        for action in self.actions:
            with self.subTest(action=action):
                response = self.perform_action(action)
                assert response.status_code == status.HTTP_200_OK

    def test_submission_cannot_set_management_state(self):
        self.client.force_authenticate(self.autor)
        response = self.client.post(
            self.url,
            {**self.payload, 'favorita': True, 'recusada': True, 'recusada_em': '2026-11-10T12:00:00Z'},
            format='json',
        )

        assert response.status_code == status.HTTP_201_CREATED
        created = SugestaoProjeto.objects.get(pk=response.data['id'])
        assert not created.favorita
        assert not created.recusada
        assert created.recusada_em is None


class SugestaoProjetoConsultaAPITests(SugestaoProjetoAPITestCase):
    def test_public_cannot_read_submissions(self):
        created = self.client.post(self.url, self.payload, format='json')
        self.client.force_authenticate(user=None)

        listing = self.client.get(self.url)
        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[created.data['id']]))

        assert listing.status_code == status.HTTP_401_UNAUTHORIZED
        assert detail.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unrelated_user_cannot_read_submissions(self):
        created = self.client.post(self.url, self.payload, format='json')
        self.client.force_authenticate(self.outro_usuario)

        listing = self.client.get(self.url)
        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[created.data['id']]))

        assert listing.status_code == status.HTTP_200_OK
        assert listing.data['results'] == []
        assert detail.status_code == status.HTTP_404_NOT_FOUND

    def test_team_students_and_professors_can_read_received_suggestions(self):
        created = self.client.post(self.url, self.payload, format='json')

        for user in [self.aluno_user, self.professor_user]:
            with self.subTest(user=user.pk):
                self.client.force_authenticate(user)
                listing = self.client.get(self.url, {'equipe': str(self.equipe.pk)})
                detail = self.client.get(reverse('sugestoes-projetos-detail', args=[created.data['id']]))

                assert listing.status_code == status.HTTP_200_OK
                assert [item['id'] for item in listing.data['results']] == [created.data['id']]
                assert detail.status_code == status.HTTP_200_OK
                assert detail.data['autor'] is None

    def test_identified_author_can_read_their_own_suggestion(self):
        self.client.force_authenticate(self.autor)
        self.payload['anonimo'] = False
        created = self.client.post(self.url, self.payload, format='json')

        listing = self.client.get(self.url)
        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[created.data['id']]))

        assert [item['id'] for item in listing.data['results']] == [created.data['id']]
        assert detail.status_code == status.HTTP_200_OK
        assert detail.data['autor']['id'] == self.autor.pk
        assert detail.data['autor']['name'] == self.autor.name
        assert 'email' not in detail.data['autor']
        assert detail.data['autor']['perfil_id'] is None
        assert detail.data['autor']['tipo'] is None
        assert detail.data['autor']['imagem_perfil'] is None

    def test_teacher_can_see_identified_student_profile_and_photo(self):
        image = Image.objects.create(file='images/autor.png')
        aluno = Aluno.objects.create(user=self.autor, data_nascimento=date(2005, 1, 1), imagem_perfil=image)
        self.autor.username = 'autor.robotica'
        self.autor.save(update_fields=['username'])
        self.payload['anonimo'] = False
        self.client.post(self.url, self.payload, format='json')
        self.client.force_authenticate(self.professor_user)

        listing = self.client.get(self.url, {'equipe': str(self.equipe.pk)}, HTTP_HOST='backend.example:8000')

        author = listing.data['results'][0]['autor']
        assert author['username'] == 'autor.robotica'
        assert author['tipo'] == 'aluno'
        assert author['perfil_id'] == str(aluno.pk)
        assert author['imagem_perfil']['url'] == 'http://backend.example:8000/media/images/autor.png'
        assert 'email' not in author

    def test_identified_teacher_profile_has_the_teacher_id(self):
        professor = self.professor_user.professor_profile
        image = Image.objects.create(file='images/professor.png')
        professor.imagem_perfil = image
        professor.save(update_fields=['imagem_perfil'])
        self.client.force_authenticate(self.professor_user)
        self.payload['anonimo'] = False
        created = self.client.post(self.url, self.payload, format='json')

        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[created.data['id']]))

        author = detail.data['autor']
        assert author['tipo'] == 'professor'
        assert author['perfil_id'] == str(professor.pk)
        assert author['imagem_perfil']['url'].endswith('/media/images/professor.png')

    def test_anonymous_suggestion_never_exposes_profile_data(self):
        suggestion = SugestaoProjeto.objects.create(
            titulo=self.payload['titulo'], equipe=self.equipe, descricao=self.payload['descricao'],
            anonimo=True, autor=self.professor_user,
        )
        self.client.force_authenticate(self.professor_user)

        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[suggestion.pk]))

        assert detail.data['autor'] is None

    def test_staff_can_read_submissions(self):
        created = self.client.post(self.url, self.payload, format='json')
        self.client.force_authenticate(self.admin)

        listing = self.client.get(self.url)
        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[created.data['id']]))

        assert [item['id'] for item in listing.data['results']] == [created.data['id']]
        assert detail.status_code == status.HTTP_200_OK

    def test_team_filter_does_not_grant_access_to_other_teams(self):
        self.payload['equipe'] = str(self.outra_equipe.pk)
        created = self.client.post(self.url, self.payload, format='json')
        self.client.force_authenticate(self.professor_user)

        response = self.client.get(self.url, {'equipe': str(self.outra_equipe.pk)})
        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[created.data['id']]))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == []
        assert detail.status_code == status.HTTP_404_NOT_FOUND

    def test_suggestions_cannot_be_updated_or_deleted_through_api(self):
        self.client.force_authenticate(self.admin)
        created = self.client.post(self.url, self.payload, format='json')
        detail_url = reverse('sugestoes-projetos-detail', args=[created.data['id']])

        for method in ['put', 'patch', 'delete']:
            with self.subTest(method=method):
                response = getattr(self.client, method)(detail_url, {}, format='json')
                assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        assert SugestaoProjeto.objects.filter(pk=created.data['id']).exists()

    def test_team_selector_filters_by_institution_and_active_status(self):
        response = self.client.get(
            reverse('equipes-list'),
            {'instituicao': str(self.instituicao.pk), 'ativo': 'true'},
        )

        assert response.status_code == status.HTTP_200_OK
        assert [item['id'] for item in response.data['items']] == [str(self.equipe.pk)]

    def test_team_selector_searches_by_partial_name_ignoring_case(self):
        Equipe.objects.create(nome='Cypher inativa', ativo=False)

        response = self.client.get(reverse('equipes-list'), {'search': 'YPH', 'ativo': 'true'})

        assert response.status_code == status.HTTP_200_OK
        assert [item['id'] for item in response.data['items']] == [str(self.equipe.pk)]

    def test_team_selector_returns_empty_items_when_no_name_matches(self):
        response = self.client.get(reverse('equipes-list'), {'search': 'inexistente', 'ativo': 'true'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['items'] == []
