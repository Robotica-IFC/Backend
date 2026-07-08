from rest_framework.viewsets import ModelViewSet

from core.models import Projeto
from core.serializers import ProjetoListSerializer, ProjetoRetrieveSerializer, ProjetoSerializer

class ProjetoViewSet(ModelViewSet):
    queryset = Projeto.objects.all()
    serializer_class = ProjetoSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ProjetoListSerializer
        elif self.action == 'retrieve':
            return ProjetoRetrieveSerializer
        return ProjetoSerializer