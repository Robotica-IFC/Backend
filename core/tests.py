from datetime import date, timedelta
from io import BytesIO
from uuid import uuid4

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image as PILImage
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from core.models import Aluno, Equipe, Estoque, Instituicao, Professor, Projeto, SugestaoProjeto, User
from core.serializers import EquipeListRetrieveSerializer, EstoqueSerializer
from uploader.models import Document, Image


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

    def test_submission_accepts_four_mixed_pdf_and_image_attachments(self):
        image_bytes = BytesIO()
        PILImage.new('RGB', (2, 2), color='blue').save(image_bytes, format='PNG')
        attachment_keys = []
        for name, content, content_type in [
            ('proposta.pdf', b'%PDF-1.4\n%%EOF', 'application/pdf'),
            ('referencia.pdf', b'%PDF-1.4\n%%EOF', 'application/pdf'),
            ('foto.png', image_bytes.getvalue(), 'image/png'),
            ('esquema.png', image_bytes.getvalue(), 'image/png'),
        ]:
            upload = self.client.post('/api/media/documents/', {
                'file': SimpleUploadedFile(name, content, content_type),
                'description': name,
            }, format='multipart')
            assert upload.status_code == status.HTTP_201_CREATED
            assert upload.data['content_type'] == content_type
            attachment_keys.append(upload.data['attachment_key'])

        response = self.client.post(self.url, {**self.payload, 'anexos': attachment_keys}, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        self.client.force_authenticate(self.professor_user)
        detail = self.client.get(reverse('sugestoes-projetos-detail', args=[response.data['id']]))
        assert len(detail.data['anexos']) == len(attachment_keys)
        for attachment in detail.data['anexos']:
            extension = '.png' if attachment['content_type'] == 'image/png' else '.pdf'
            assert attachment['url'].endswith(extension)

    def test_more_than_four_attachments_are_rejected(self):
        attachments = [Document.objects.create(file=f'documents/{index}.pdf') for index in range(5)]

        response = self.client.post(self.url, {
            **self.payload, 'anexos': [str(document.attachment_key) for document in attachments],
        }, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'anexos' in response.data
        assert not SugestaoProjeto.objects.exists()

    def test_upload_rejects_files_disguised_as_an_image(self):
        response = self.client.post('/api/media/documents/', {
            'file': SimpleUploadedFile('foto.png', b'not an image', 'image/png'),
        }, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'file' in response.data

    def test_upload_detects_content_type_instead_of_trusting_the_client(self):
        image_bytes = BytesIO()
        PILImage.new('RGB', (2, 2)).save(image_bytes, format='PNG')

        response = self.client.post('/api/media/documents/', {
            'file': SimpleUploadedFile('foto.png', image_bytes.getvalue(), 'image/png'),
            'content_type': 'application/pdf',
        }, format='multipart')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content_type'] == 'image/png'


class SugestaoProjetoFavoritosAPITests(SugestaoProjetoAPITestCase):
    def setUp(self):
        super().setUp()
        self.suggestion = SugestaoProjeto.objects.create(
            titulo=self.payload['titulo'], descricao=self.payload['descricao'],
            equipe=self.equipe, autor=self.autor, anonimo=False,
        )
        self.favorite_url = reverse('sugestoes-projetos-favoritar', args=[self.suggestion.pk])
        self.unfavorite_url = reverse('sugestoes-projetos-desfavoritar', args=[self.suggestion.pk])
        self.detail_url = reverse('sugestoes-projetos-detail', args=[self.suggestion.pk])

    def test_favorite_persists_and_can_be_removed_idempotently(self):
        self.client.force_authenticate(self.professor_user)

        response = self.client.post(self.favorite_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['favorita'] is True
        assert response.data['recusada'] is False
        self.client.post(self.favorite_url)
        assert self.suggestion.favoritada_por.count() == 1
        assert self.client.get(self.detail_url).data['favorita'] is True
        assert self.client.get(self.url).data['results'][0]['favorita'] is True

        removed = self.client.post(self.unfavorite_url)

        assert removed.status_code == status.HTTP_200_OK
        assert removed.data['favorita'] is False
        self.client.post(self.unfavorite_url)
        assert not self.suggestion.favoritada_por.exists()
        assert self.client.get(self.detail_url).data['favorita'] is False

    def test_favorites_are_individual_for_each_team_teacher(self):
        second_teacher = Professor.objects.create(
            user=self.outro_usuario, cpf='98765432100', telefone='47988888888',
            data_nascimento=date(1990, 1, 1), instituicao=self.instituicao,
        )
        self.equipe.professores.add(second_teacher)
        self.client.force_authenticate(self.professor_user)
        self.client.post(self.favorite_url)
        self.client.force_authenticate(self.outro_usuario)

        assert self.client.get(self.detail_url).data['favorita'] is False
        self.client.post(self.favorite_url)
        self.client.force_authenticate(self.professor_user)
        self.client.post(self.unfavorite_url)
        assert self.client.get(self.detail_url).data['favorita'] is False
        self.client.force_authenticate(self.outro_usuario)
        assert self.client.get(self.detail_url).data['favorita'] is True

    def test_author_student_and_unrelated_user_cannot_manage_favorites(self):
        for user, expected_status in [
            (self.autor, status.HTTP_403_FORBIDDEN),
            (self.aluno_user, status.HTTP_403_FORBIDDEN),
            (self.outro_usuario, status.HTTP_404_NOT_FOUND),
        ]:
            self.client.force_authenticate(user)
            for url in [self.favorite_url, self.unfavorite_url]:
                with self.subTest(user=user.pk, url=url):
                    assert self.client.post(url).status_code == expected_status
        assert not self.suggestion.favoritada_por.exists()

    def test_favoriting_requires_authentication_and_allows_staff(self):
        self.client.force_authenticate(user=None)
        assert self.client.post(self.favorite_url).status_code == status.HTTP_401_UNAUTHORIZED
        self.client.force_authenticate(self.admin)
        assert self.client.post(self.favorite_url).data['favorita'] is True
        assert self.client.post(self.unfavorite_url).data['favorita'] is False

    def test_favorite_survives_rejection_and_restoration_without_revealing_anonymous_author(self):
        self.suggestion.anonimo = True
        self.suggestion.save(update_fields=['anonimo'])
        self.client.force_authenticate(self.professor_user)
        self.client.post(self.favorite_url)

        rejected = self.client.post(reverse('sugestoes-projetos-recusar', args=[self.suggestion.pk]))

        assert rejected.data['favorita'] is True
        assert rejected.data['recusada'] is True
        assert rejected.data['autor'] is None
        restored = self.client.post(reverse('sugestoes-projetos-aceitar', args=[self.suggestion.pk]))
        assert restored.data['favorita'] is True
        assert restored.data['recusada'] is False
        assert restored.data['autor'] is None

    def test_submission_cannot_assign_favorites(self):
        response = self.client.post(self.url, {
            **self.payload, 'favorita': True, 'favoritada_por': [self.professor_user.pk],
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['favorita'] is False
        assert not SugestaoProjeto.objects.get(pk=response.data['id']).favoritada_por.exists()


class SugestaoProjetoModeracaoAPITests(SugestaoProjetoAPITestCase):
    def setUp(self):
        super().setUp()
        self.suggestion = SugestaoProjeto.objects.create(
            titulo=self.payload['titulo'], descricao=self.payload['descricao'],
            equipe=self.equipe, autor=self.autor, anonimo=False,
        )
        self.reject_url = reverse('sugestoes-projetos-recusar', args=[self.suggestion.pk])
        self.accept_url = reverse('sugestoes-projetos-aceitar', args=[self.suggestion.pk])

    def test_team_teacher_can_reject_and_restore_without_losing_content(self):
        attachment = Document.objects.create(file='documents/proposta.pdf')
        self.suggestion.anexos.add(attachment)
        original_date = self.suggestion.criado_em
        self.client.force_authenticate(self.professor_user)

        rejected = self.client.post(self.reject_url)

        assert rejected.status_code == status.HTTP_200_OK
        assert rejected.data['recusada'] is True
        assert rejected.data['recusada_em'] is not None
        assert rejected.data['autor']['id'] == self.autor.pk
        assert rejected.data['anexos'][0]['attachment_key'] == str(attachment.attachment_key)
        self.suggestion.refresh_from_db()
        first_rejection_date = self.suggestion.recusada_em
        self.client.post(self.reject_url)
        self.suggestion.refresh_from_db()
        assert self.suggestion.recusada_em == first_rejection_date

        accepted = self.client.post(self.accept_url)

        assert accepted.status_code == status.HTTP_200_OK
        assert accepted.data['recusada'] is False
        assert accepted.data['recusada_em'] is None
        self.suggestion.refresh_from_db()
        assert self.suggestion.criado_em == original_date
        assert self.suggestion.anexos.count() == 1
        assert not Projeto.objects.exists()

    def test_author_and_team_student_cannot_change_rejection(self):
        for user in [self.autor, self.aluno_user]:
            for url in [self.reject_url, self.accept_url]:
                with self.subTest(user=user.pk, url=url):
                    self.client.force_authenticate(user)

                    response = self.client.post(url)

                    assert response.status_code == status.HTTP_403_FORBIDDEN
        self.suggestion.refresh_from_db()
        assert not self.suggestion.recusada

    def test_unrelated_user_and_teacher_cannot_moderate_other_team(self):
        self.client.force_authenticate(self.outro_usuario)
        assert self.client.post(self.reject_url).status_code == status.HTTP_404_NOT_FOUND
        other_suggestion = SugestaoProjeto.objects.create(
            titulo='Outra sugestão', descricao='Outra equipe', equipe=self.outra_equipe,
        )
        self.client.force_authenticate(self.professor_user)
        for action in ['recusar', 'aceitar']:
            url = reverse(f'sugestoes-projetos-{action}', args=[other_suggestion.pk])
            assert self.client.post(url).status_code == status.HTTP_404_NOT_FOUND

    def test_public_cannot_moderate_and_staff_can(self):
        self.client.force_authenticate(user=None)
        for url in [self.reject_url, self.accept_url]:
            assert self.client.post(url).status_code == status.HTTP_401_UNAUTHORIZED
        self.client.force_authenticate(self.admin)
        assert self.client.post(self.reject_url).data['recusada'] is True
        assert self.client.post(self.accept_url).data['recusada'] is False

    def test_rejected_filter_and_status_survive_a_new_request(self):
        self.client.force_authenticate(self.professor_user)
        self.client.post(self.reject_url)

        rejected = self.client.get(self.url, {'equipe': str(self.equipe.pk), 'recusada': 'true'})
        available = self.client.get(self.url, {'equipe': str(self.equipe.pk), 'recusada': 'false'})

        assert [item['id'] for item in rejected.data['results']] == [self.suggestion.pk]
        assert available.data['results'] == []
        self.client.post(self.accept_url)
        restored = self.client.get(self.url, {'recusada': 'false'})
        assert [item['id'] for item in restored.data['results']] == [self.suggestion.pk]

    def test_rejected_anonymous_suggestion_keeps_identity_hidden(self):
        self.suggestion.anonimo = True
        self.suggestion.save(update_fields=['anonimo'])
        self.client.force_authenticate(self.professor_user)

        response = self.client.post(self.reject_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['autor'] is None

    def test_submission_cannot_override_rejection_fields(self):
        response = self.client.post(self.url, {
            **self.payload, 'recusada': True, 'recusada_em': timezone.now().isoformat(),
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['recusada'] is False
        assert response.data['recusada_em'] is None

    def test_lists_support_four_per_page_in_reverse_creation_order(self):
        created = [self.suggestion]
        for index in range(8):
            created.append(SugestaoProjeto.objects.create(
                titulo=f'Sugestão {index}', descricao='Teste', equipe=self.equipe,
            ))
        now = timezone.now()
        for index, suggestion in enumerate(created):
            SugestaoProjeto.objects.filter(pk=suggestion.pk).update(criado_em=now + timedelta(seconds=index))
        self.client.force_authenticate(self.professor_user)
        result_ids = []
        page_size = 4
        total_pages = (len(created) + page_size - 1) // page_size
        for page in range(1, total_pages + 1):
            response = self.client.get(self.url, {'page_size': page_size, 'page': page})

            assert response.status_code == status.HTTP_200_OK
            assert response.data['total_pages'] == total_pages
            assert len(response.data['results']) <= page_size
            result_ids.extend(item['id'] for item in response.data['results'])
        assert result_ids == [suggestion.pk for suggestion in reversed(created)]


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
