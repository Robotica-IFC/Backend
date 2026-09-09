from rest_framework.viewsets import ModelViewSet

from core.models import Estoque, Item
from core.serializers import EstoqueSerializer, ItemSerializer


class EstoqueViewSet(ModelViewSet):
    queryset = Estoque.objects.all()
    serializer_class = EstoqueSerializer


class ItemViewSet(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
