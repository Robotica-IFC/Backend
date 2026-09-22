from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.models import Estoque, Item
from core.serializers import EstoqueSerializer, ItemSerializer


class EstoqueViewSet(ModelViewSet):
    queryset = Estoque.objects.all()
    serializer_class = EstoqueSerializer


class ItemViewSet(ModelViewSet):
    serializer_class = ItemSerializer
    def get_queryset(self):
        queryset = Item.objects.all()

        # Lê o parâmetro ?estoque=1 enviado na URL
        estoque_id = self.request.query_params.get('estoque')

        # Filtra a lista para retornar APENAS os itens desse estoque
        if estoque_id is not None:
            queryset = queryset.filter(estoque_id=estoque_id)

        return queryset
