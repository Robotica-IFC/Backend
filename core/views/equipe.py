from rest_framework import mixins, viewsets

from core.models import Equipe
from core.serializers import EquipeSerializer
from core.pagination import EquipePagination

class EquipeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet
):
    queryset = Equipe.objects.all()
    serializer_class = EquipeSerializer
    pagination_class = EquipePagination

    def perform_create(self, serializer):
        equipe = serializer.save()

        primeiro_professor = equipe.professores.first()

        if primeiro_professor:
            equipe.instituicao = primeiro_professor.instituicao
            equipe.save(update_fields=["instituicao"])