from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.models import Equipe
from core.pagination import EquipePagination
from core.serializers import (
    EquipeCardSerializer,
    EquipeListRetrieveSerializer,
    EquipeOpcaoSerializer,
    EquipeSerializer,
    SairEquipeSerializer,
)


class EquipeViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Equipe.objects.all()
    serializer_class = EquipeSerializer
    pagination_class = EquipePagination

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['categorias__nome', 'instituicao__nome', 'instituicao', 'ativo']
    search_fields = ['nome']
    ordering = ['-views']

    permission_classes = [IsAuthenticatedOrReadOnly]

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

    def perform_create(self, serializer):
        equipe = serializer.save()

        primeiro_professor = equipe.professores.first()

        if primeiro_professor:
            equipe.instituicao = primeiro_professor.instituicao
            equipe.save(update_fields=['instituicao'])
