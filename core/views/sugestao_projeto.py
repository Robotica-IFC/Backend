from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
        if self.action == 'create':
            return SugestaoProjetoSerializer
        return SugestaoProjetoListRetrieveSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()

        queryset = super().get_queryset().select_related(
            'equipe', 'autor__aluno_profile__imagem_perfil', 'autor__professor_profile__imagem_perfil',
        ).prefetch_related('anexos')
        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(autor=user) | Q(equipe__alunos__user=user) | Q(equipe__professores__user=user)
        ).distinct()

    def _get_manageable_suggestion(self):
        suggestion = self.get_object()
        user = self.request.user
        if not user.is_staff and not suggestion.equipe.professores.filter(user=user).exists():
            raise PermissionDenied('Apenas professores desta equipe podem gerenciar sugestões.')
        return suggestion

    def _save_state(self, suggestion, **changes):
        for field, value in changes.items():
            setattr(suggestion, field, value)
        suggestion.save(update_fields=list(changes))
        return Response(self.get_serializer(suggestion).data)

    @action(detail=True, methods=['post'])
    def favoritar(self, request, pk=None):
        return self._save_state(self._get_manageable_suggestion(), favorita=True)

    @action(detail=True, methods=['post'])
    def desfavoritar(self, request, pk=None):
        return self._save_state(self._get_manageable_suggestion(), favorita=False)

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        suggestion = self._get_manageable_suggestion()
        return self._save_state(
            suggestion, recusada=True, recusada_em=suggestion.recusada_em or timezone.now(),
        )

    @action(detail=True, methods=['post'])
    def aceitar(self, request, pk=None):
        return self._save_state(self._get_manageable_suggestion(), recusada=False, recusada_em=None)
