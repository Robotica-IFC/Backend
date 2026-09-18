from django.db.models import F, Q
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Equipe
from core.pagination import EquipePagination
from core.serializers import (
    EquipeCardSerializer,
    EquipeListRetrieveSerializer,
    EquipeSerializer,
)


class EquipeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Equipe.objects.all()
    serializer_class = EquipeSerializer
    pagination_class = EquipePagination

    def get_queryset(self):
        """
        Sobrescreve o queryset para ordenar pelas equipes com mais visualizações
        e otimizar o carregamento de relacionamentos no BD.
        """
        queryset = Equipe.objects.all().order_by('-views')

        # Otimização de performance para evitar N+1 queries na listagem/detalhes
        if self.action in ['list', 'retrieve']:
            queryset = queryset.select_related('instituicao').prefetch_related(
                'alunos__user',
                'professores__user',
            )

        return queryset

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return EquipeListRetrieveSerializer
        elif self.action == 'por_usuario':
            return EquipeCardSerializer
        return EquipeSerializer

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
        equipes = self.get_queryset().filter(
            Q(alunos__user__id=user_id) | Q(professores__user__id=user_id)
        ).distinct()

        serializer = self.get_serializer(equipes, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        equipe = serializer.save()

        primeiro_professor = equipe.professores.first()

        if primeiro_professor:
            equipe.instituicao = primeiro_professor.instituicao
            equipe.save(update_fields=["instituicao"])