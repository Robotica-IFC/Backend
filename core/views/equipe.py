from rest_framework import mixins, viewsets

from core.models import Equipe
from core.pagination import EquipePagination
from core.serializers import EquipeListRetrieveSerializer, EquipeSerializer


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
        return EquipeSerializer

    def perform_create(self, serializer):
        equipe = serializer.save()

        primeiro_professor = equipe.professores.first()

        if primeiro_professor:
            equipe.instituicao = primeiro_professor.instituicao
            equipe.save(update_fields=["instituicao"])