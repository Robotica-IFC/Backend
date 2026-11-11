from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from core.models import Notificacao
from core.serializers.notificacao import NotificacaoSerializer


class NotificacaoPagination(PageNumberPagination):
    page_size = 20


class NotificacaoViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificacaoSerializer
    pagination_class = NotificacaoPagination

    def get_queryset(self):
        return Notificacao.objects.filter(destinatario=self.request.user).select_related('projeto__equipe')

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data['nao_lidas'] = self.get_queryset().filter(lida_em__isnull=True).count()
        return response

    @action(detail=False, methods=['get'], url_path='nao-lidas')
    def nao_lidas(self, request):
        queryset = self.get_queryset().filter(lida_em__isnull=True)
        return Response({'nao_lidas': queryset.count(), 'ultima_nao_lida': queryset.values_list('id', flat=True).first()})

    @action(detail=True, methods=['post'], url_path='ler')
    def ler(self, request, pk=None):
        notificacao = self.get_object()
        # Leituras repetidas preservam o instante original, inclusive entre abas.
        self.get_queryset().filter(pk=notificacao.pk, lida_em__isnull=True).update(lida_em=timezone.now())
        notificacao.refresh_from_db()
        return Response(self.get_serializer(notificacao).data)
