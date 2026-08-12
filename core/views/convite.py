from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Convite
from core.serializers import (
    ConviteCreateSerializer,
    ConviteListRetrieveSerializer,
    ConviteSerializer,
)


class ConviteViewSet(ModelViewSet):
    queryset = Convite.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'list', 'retrieve'}:
            return ConviteListRetrieveSerializer
        if self.action == 'create':
            return ConviteCreateSerializer
        return ConviteSerializer
