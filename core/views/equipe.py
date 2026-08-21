from django.db.models import Q
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

    def get_serializer_class(self):
        if self.action == 'list':
            return EquipeListRetrieveSerializer
        elif self.action == 'retrieve':
            return EquipeListRetrieveSerializer
        elif self.action == 'por_usuario':
            return EquipeCardSerializer
        return EquipeSerializer

    @action(detail=False, methods=['get'], url_path='usuario/(?P<user_id>[^/.]+)')
    def por_usuario(self, request, user_id=None):
        """
        Busca equipes que contenham o usuário informado, seja ele Aluno ou Professor.
        Retorna apenas os dados resumidos do EquipeCardSerializer.
        """
        equipes = Equipe.objects.filter(
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
