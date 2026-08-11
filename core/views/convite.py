from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from core.models import Convite, Professor
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

    def perform_create(self, serializer):
        try:
            professor = Professor.objects.get(usuario=self.request.user) # Ou user=self.request.user
            serializer.save(convidante=professor)
        except Professor.DoesNotExist:
            raise ValidationError({'convidante': 'O usuário autenticado não possui um perfil de Professor associado.'})