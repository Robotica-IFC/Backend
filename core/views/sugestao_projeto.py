from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from core.models import SugestaoProjeto
from core.serializers import SugestaoProjetoListRetrieveSerializer, SugestaoProjetoSerializer


class SugestaoProjetoViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = SugestaoProjeto.objects.all()
    serializer_class = SugestaoProjetoSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'head', 'options']
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['equipe', 'anonimo']

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return SugestaoProjetoListRetrieveSerializer
        return SugestaoProjetoSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()

        queryset = super().get_queryset().select_related('equipe', 'autor').prefetch_related('anexos')
        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(autor=user) | Q(equipe__alunos__user=user) | Q(equipe__professores__user=user)
        ).distinct()
