from django.db.models import Case, Exists, OuterRef, Q, When
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import Equipe, SugestaoProjeto
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
    filterset_fields = ['equipe', 'anonimo', 'recusada']

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve', 'recusar', 'aceitar', 'favoritar', 'desfavoritar'}:
            return SugestaoProjetoListRetrieveSerializer
        return SugestaoProjetoSerializer

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return self.queryset.none()

        favorites = SugestaoProjeto.favoritada_por.through.objects.filter(
            sugestaoprojeto_id=OuterRef('pk'),
        )
        favorite_status = Exists(favorites.filter(user_id=user.pk))
        if not user.is_staff:
            student_membership = Equipe.alunos.through.objects.filter(
                equipe_id=OuterRef('equipe_id'), aluno__user=user,
            )
            teacher_membership = Equipe.professores.through.objects.filter(
                equipe_id=OuterRef('equipe_id'), professor__user=user,
            )
            # Alunos visualizam as favoritas dos professores; professores mantêm sua seleção pessoal.
            favorite_status = Case(
                When(
                    Exists(student_membership) & ~Exists(teacher_membership),
                    then=Exists(favorites.filter(user__professor_profile__equipes=OuterRef('equipe_id'))),
                ),
                default=favorite_status,
            )

        queryset = super().get_queryset().select_related(
            'equipe', 'autor__aluno_profile__imagem_perfil', 'autor__professor_profile__imagem_perfil',
        ).prefetch_related('anexos').annotate(
            favorita=favorite_status,
        )
        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(autor=user) | Q(equipe__alunos__user=user) | Q(equipe__professores__user=user)
        ).distinct()

    def ensure_team_teacher(self, suggestion):
        user = self.request.user
        if not user.is_staff and not suggestion.equipe.professores.filter(user=user).exists():
            raise PermissionDenied('Apenas professores vinculados à equipe podem gerenciar sugestões.')

    def set_rejected(self, rejected):
        suggestion = self.get_object()
        self.ensure_team_teacher(suggestion)
        if suggestion.recusada != rejected:
            suggestion.recusada = rejected
            suggestion.recusada_em = timezone.now() if rejected else None
            suggestion.save(update_fields=['recusada', 'recusada_em'])
        return Response(self.get_serializer(suggestion).data)

    @action(detail=True, methods=['post'])
    def recusar(self, request, pk=None):
        return self.set_rejected(True)

    @action(detail=True, methods=['post'])
    def aceitar(self, request, pk=None):
        return self.set_rejected(False)

    def set_favorite(self, favorite):
        suggestion = self.get_object()
        self.ensure_team_teacher(suggestion)
        if favorite:
            suggestion.favoritada_por.add(self.request.user)
        else:
            suggestion.favoritada_por.remove(self.request.user)
        suggestion.favorita = favorite
        return Response(self.get_serializer(suggestion).data)

    @action(detail=True, methods=['post'])
    def favoritar(self, request, pk=None):
        return self.set_favorite(True)

    @action(detail=True, methods=['post'])
    def desfavoritar(self, request, pk=None):
        return self.set_favorite(False)
