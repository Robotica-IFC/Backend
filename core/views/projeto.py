from rest_framework.viewsets import ModelViewSet

from core.models import Projeto
from core.serializers import ProjetoListSerializer, ProjetoRetrieveSerializer, ProjetoSerializer

class ProjetoViewSet(ModelViewSet):
    queryset = Projeto.objects.all()

    def get_queryset(self):
        queryset = super().get_queryset()

        equipe = self.request.query_params.get("equipe")

        if equipe:
            queryset = queryset.filter(equipe_id=equipe)

        return queryset
    def get_serializer_class(self):
        if self.action == 'list':
            return ProjetoListSerializer
        elif self.action == 'retrieve':
            return ProjetoRetrieveSerializer
        return ProjetoSerializer