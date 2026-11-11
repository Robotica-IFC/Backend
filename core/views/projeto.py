from django.db import transaction
from django.db.models import OuterRef, Subquery
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Equipe, Projeto
from core.permissions_social import CanEditProject
from core.serializers import (
    ProjetoDetailWithPostsSerializer,
    ProjetoListSerializer,
    ProjetoRetrieveSerializer,
    ProjetoSerializer,
)
from core.serializers.projeto import ProjetoDestaqueSerializer


class ProjetoViewSet(ModelViewSet):
    queryset = Projeto.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, CanEditProject]

    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save()

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

    @action(detail=False, methods=['get'])
    def destaques(self, request):
        equipes = Equipe.objects.order_by('-views', 'pk').values('pk')[:3]
        mais_recente = Projeto.objects.filter(equipe_id=OuterRef('equipe_id')).order_by(
            '-data_criacao', '-pk',
        ).values('pk')[:1]
        projetos = Projeto.objects.filter(
            equipe_id__in=Subquery(equipes), pk=Subquery(mais_recente),
        ).select_related('equipe__image_perfil', 'image_perfil').order_by('-equipe__views', 'equipe_id')
        return Response(ProjetoDestaqueSerializer(projetos, many=True, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['get'], url_path='posts')
    def get_projeto_com_posts(self, request, pk=None):
        projeto = self.get_object()
        serializer = self.get_serializer(projeto)
        return Response(serializer.data)
