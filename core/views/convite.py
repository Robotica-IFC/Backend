from django.db import transaction
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError, NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Convite
from core.serializers import ConviteCreateSerializer, ConviteListRetrieveSerializer


class ConviteViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']

    def get_queryset(self):
        user = self.request.user
        queryset = Convite.objects.select_related('equipe', 'convidante__user', 'aluno__user', 'professor__user')
        if user.is_staff:
            return queryset
        return queryset.filter(
            Q(aluno__user=user) | Q(professor__user=user) | Q(convidante__user=user)
        ).distinct()

    def get_serializer_class(self):
        if self.action == 'create':
            return ConviteCreateSerializer
        return ConviteListRetrieveSerializer

    @action(detail=False, methods=['get'], url_path='recebidos')
    def recebidos(self, request):
        convites = self.get_queryset().filter(
            Q(aluno__user=request.user) | Q(professor__user=request.user)
        ).order_by('-pk')
        return Response(self.get_serializer(convites, many=True).data)

    def _responder(self, request, pk, aceitar):
        with transaction.atomic():
            convite = self.get_queryset().select_for_update().filter(pk=pk).first()
            if not convite:
                raise NotFound('Convite não encontrado.')
            destinatario_id = convite.aluno.user_id if convite.aluno_id else convite.professor.user_id
            if destinatario_id != request.user.pk:
                raise PermissionDenied('Somente o destinatário pode responder.')
            if convite.status != Convite.StatusChoices.PENDENTE:
                raise ValidationError('Este convite já foi respondido.')
            if aceitar:
                if convite.aluno_id:
                    convite.equipe.alunos.add(convite.aluno)
                else:
                    convite.equipe.professores.add(convite.professor)
            convite.status = Convite.StatusChoices.ACEITO if aceitar else Convite.StatusChoices.NEGADO
            convite.save(update_fields=['status'])
            return Response(self.get_serializer(convite).data)

    @action(detail=True, methods=['post'], url_path='aceitar')
    def aceitar(self, request, pk=None):
        return self._responder(request, pk, True)

    @action(detail=True, methods=['post'], url_path='recusar')
    def recusar(self, request, pk=None):
        return self._responder(request, pk, False)
