from django.db import transaction
from django.utils import timezone
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework import status

from core.permissions_social import CanEditTeam
from core.serializers.equipe import TransferirOwnerSerializer
from core.models import Equipe, SolicitacaoEquipe
from core.pagination import EquipePagination
from core.serializers import (
    EquipeCardSerializer,
    EquipeListRetrieveSerializer,
    EquipeOpcaoSerializer,
    EquipeSerializer,
    SairEquipeSerializer,
)


class EquipeViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Equipe.objects.all()
    serializer_class = EquipeSerializer
    pagination_class = EquipePagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['categorias__nome', 'instituicao__nome', 'instituicao', 'ativo']
    search_fields = ['nome']
    ordering = ['-views']

    permission_classes = [IsAuthenticatedOrReadOnly, CanEditTeam]

    def get_queryset(self):
        """
        Sobrescreve o queryset para ordenar pelas equipes com mais visualizações
        e otimizar o carregamento de relacionamentos no BD.
        """
        queryset = Equipe.objects.all().order_by('-views')

        if self.action == 'opcoes':
            return queryset.select_related('image_perfil')

        # Otimização de performance para evitar N+1 queries na listagem/detalhes
        if self.action in {'list', 'retrieve'}:
            queryset = queryset.select_related('instituicao').prefetch_related(
                'alunos__user',
                'professores__user',
            )

        return queryset

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return EquipeListRetrieveSerializer
        elif self.action == 'por_usuario':
            return EquipeCardSerializer
        elif self.action == 'opcoes':
            return EquipeOpcaoSerializer
        return EquipeSerializer

    def get_locked_team(self, pk):
        equipe = get_object_or_404(Equipe.objects.select_for_update(), pk=pk)
        self.check_object_permissions(self.request, equipe)
        return equipe

    def require_owner(self, equipe):
        if not equipe.criador_id or equipe.criador.user_id != self.request.user.pk:
            raise PermissionDenied('Somente o OWNER da equipe pode realizar esta ação.')

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        equipe = self.get_locked_team(kwargs['pk'])
        self.require_owner(equipe)
        # Convites protegem a equipe por padrão; a exclusão explícita inclui seu histórico.
        equipe.convites.all().delete()
        equipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='transferir-owner')
    @transaction.atomic
    def transferir_owner(self, request, pk=None):
        equipe = self.get_locked_team(pk)
        self.require_owner(equipe)
        serializer = TransferirOwnerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        professor = equipe.professores.filter(pk=serializer.validated_data['professor']).first()
        if professor is None:
            raise ValidationError({'professor': 'O novo OWNER precisa ser professor desta equipe.'})
        if professor.pk == equipe.criador_id:
            raise ValidationError({'professor': 'Este professor já é o OWNER da equipe.'})
        equipe.criador = professor
        equipe.save(update_fields=['criador'])
        return Response(EquipeListRetrieveSerializer(equipe, context=self.get_serializer_context()).data)

    @action(detail=False, methods=['get'], url_path='opcoes')
    def opcoes(self, request):
        """Lista opções de equipes com nome e imagem, aplicando filtros e paginação."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post', 'get'], url_path='visualizar')
    def incrementar_views(self, request, pk=None):
        """
        Incrementa +1 no contador de views da equipe e retorna o objeto atualizado.
        Endpoint: /api/equipes/{id}/visualizar/
        """
        equipe = self.get_object()

        # Incrementa no banco de dados com atômico F() contra race condition
        Equipe.objects.filter(pk=equipe.pk).update(views=F('views') + 1)

        # Recarrega a instância para pegar o valor correto de 'views' atualizado
        equipe.refresh_from_db()

        serializer = self.get_serializer(equipe)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='usuario/(?P<user_id>[^/.]+)')
    def por_usuario(self, request, user_id=None):
        """
        Busca equipes que contenham o usuário informado, seja ele Aluno ou Professor.
        Retorna apenas os dados resumidos do EquipeCardSerializer.
        """
        equipes = self.get_queryset().filter(Q(alunos__user__id=user_id) | Q(professores__user__id=user_id)).distinct()

        serializer = self.get_serializer(equipes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='sair', permission_classes=[IsAuthenticated])
    @transaction.atomic
    def sair(self, request, pk=None):
        equipe = get_object_or_404(Equipe.objects.select_for_update(), pk=pk)
        self.check_object_permissions(request, equipe)

        serializer = SairEquipeSerializer(data=request.data, context={'request': request, 'equipe': equipe})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'detail': 'Saída da equipe realizada com sucesso.'}, status=200)

    @action(detail=True, methods=['delete'], url_path=r'membros/(?P<membro_id>[^/.]+)', permission_classes=[IsAuthenticated])
    @transaction.atomic
    def remover_membro(self, request, pk=None, membro_id=None):
        equipe = self.get_locked_team(pk)
        self.require_owner(equipe)
        tipo = request.query_params.get('tipo')
        if tipo == 'aluno':
            membro = equipe.alunos.filter(pk=membro_id).first()
            if membro is None:
                raise ValidationError({'membro': 'Aluno não pertence à equipe.'})
            equipe.alunos.remove(membro)
        elif tipo == 'professor':
            membro = equipe.professores.filter(pk=membro_id).first()
            if membro is None:
                raise ValidationError({'membro': 'Professor não pertence à equipe.'})
            if membro.pk == equipe.criador_id:
                raise ValidationError({'membro': 'O OWNER não pode ser removido. Transfira a responsabilidade primeiro.'})
            equipe.professores.remove(membro)
        else:
            raise ValidationError({'tipo': 'Informe aluno ou professor.'})
        return Response(status=status.HTTP_204_NO_CONTENT)


    def _solicitacao_data(self, solicitacao):
        return {
            'id': solicitacao.pk,
            'equipe': str(solicitacao.equipe_id),
            'solicitante': solicitacao.solicitante_id,
            'nome': solicitacao.solicitante.name or solicitacao.solicitante.username or solicitacao.solicitante.email,
            'status': solicitacao.status,
            'criada_em': solicitacao.criada_em,
        }

    @action(detail=True, methods=['get'], url_path='minha-solicitacao', permission_classes=[IsAuthenticated])
    def minha_solicitacao(self, request, pk=None):
        equipe = get_object_or_404(Equipe, pk=pk)
        solicitacao = SolicitacaoEquipe.objects.filter(equipe=equipe, solicitante=request.user).first()
        return Response({'status': solicitacao.status if solicitacao else None})

    @action(detail=True, methods=['post'], url_path='solicitar', permission_classes=[IsAuthenticated])
    @transaction.atomic
    def solicitar(self, request, pk=None):
        equipe = get_object_or_404(Equipe.objects.select_for_update(), pk=pk)
        if not equipe.ativo:
            raise ValidationError('A equipe está inativa.')
        if equipe.professores.filter(user=request.user).exists() or equipe.alunos.filter(user=request.user).exists():
            raise ValidationError('Você já participa desta equipe.')
        aluno = getattr(request.user, 'aluno_profile', None)
        professor = getattr(request.user, 'professor_profile', None)
        if aluno is None and professor is None:
            raise PermissionDenied('Somente alunos ou professores cadastrados podem solicitar entrada.')

        solicitacao, created = SolicitacaoEquipe.objects.get_or_create(
            equipe=equipe, solicitante=request.user,
        )
        if not created:
            if solicitacao.status == SolicitacaoEquipe.Status.PENDENTE:
                raise ValidationError('Você já possui uma solicitação pendente.')
            # Permite solicitar novamente depois de uma recusa, sem duplicar registros.
            solicitacao.status = SolicitacaoEquipe.Status.PENDENTE
            solicitacao.criada_em = timezone.now()
            solicitacao.save(update_fields=['status', 'criada_em'])
        return Response(self._solicitacao_data(solicitacao), status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='solicitacoes', permission_classes=[IsAuthenticated])
    def solicitacoes(self, request, pk=None):
        equipe = get_object_or_404(Equipe, pk=pk)
        if not equipe.professores.filter(user=request.user).exists():
            raise PermissionDenied('Somente professores da equipe podem consultar solicitações.')
        qs = equipe.solicitacoes.filter(status=SolicitacaoEquipe.Status.PENDENTE).select_related('solicitante')
        return Response([self._solicitacao_data(item) for item in qs])

    @action(detail=True, methods=['post'], url_path=r'solicitacoes/(?P<solicitacao_id>[^/.]+)/responder', permission_classes=[IsAuthenticated])
    @transaction.atomic
    def responder_solicitacao(self, request, pk=None, solicitacao_id=None):
        equipe = get_object_or_404(Equipe.objects.select_for_update(), pk=pk)
        if not equipe.professores.filter(user=request.user).exists():
            raise PermissionDenied('Somente professores da equipe podem responder solicitações.')
        solicitacao = get_object_or_404(
            SolicitacaoEquipe.objects.select_for_update().select_related('solicitante'),
            pk=solicitacao_id, equipe=equipe,
        )
        if solicitacao.status != SolicitacaoEquipe.Status.PENDENTE:
            raise ValidationError('Solicitação já respondida.')
        aceitar = request.data.get('aceitar')
        if not isinstance(aceitar, bool):
            raise ValidationError({'aceitar': 'Informe true ou false.'})
        if aceitar:
            aluno = getattr(solicitacao.solicitante, 'aluno_profile', None)
            professor = getattr(solicitacao.solicitante, 'professor_profile', None)
            if aluno is not None:
                equipe.alunos.add(aluno)
            elif professor is not None:
                equipe.professores.add(professor)
            else:
                raise ValidationError('Solicitante não possui perfil de aluno ou professor.')
        solicitacao.status = SolicitacaoEquipe.Status.ACEITA if aceitar else SolicitacaoEquipe.Status.RECUSADA
        solicitacao.save(update_fields=['status'])
        return Response(self._solicitacao_data(solicitacao))

    def perform_create(self, serializer):
        professor = getattr(self.request.user, 'professor_profile', None)
        if professor is None:
            raise PermissionDenied('Apenas professores podem criar equipes.')
        equipe = serializer.save(criador=professor)
        equipe.professores.add(professor)

        primeiro_professor = equipe.professores.first()

        if primeiro_professor:
            equipe.instituicao = primeiro_professor.instituicao
            equipe.save(update_fields=['instituicao'])
