from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Projeto
from core.serializers import (
    ProjetoDetailWithPostsSerializer,
    ProjetoListSerializer,
    ProjetoRetrieveSerializer,
    ProjetoSerializer,
)


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
        elif self.action == 'get_projeto_com_posts':
            return ProjetoDetailWithPostsSerializer
        return ProjetoSerializer

    @action(detail=True, methods=['get'], url_path='posts')
    def get_projeto_com_posts(self, request, pk=None):
        projeto = self.get_object()
        serializer = self.get_serializer(projeto)
        return Response(serializer.data)