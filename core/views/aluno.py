from rest_framework.permissions import AllowAny
from rest_framework.filters import SearchFilter
from rest_framework.viewsets import ModelViewSet

from core.models import Aluno
from core.serializers import AlunoListSerializer, AlunoRetrieveSerializer, AlunoSerializer


class AlunoViewSet(ModelViewSet):
    queryset = Aluno.objects.all()
    filter_backends = [SearchFilter]
    search_fields = ['user__name', 'user__username']
    serializer_class = AlunoSerializer
    permission_classes = [AllowAny]  # permite a criação de usuarios por qualquer usuario

    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

    def get_serializer_class(self):
        if self.action == 'list':
            return AlunoListSerializer
        elif self.action == 'retrieve':
            return AlunoRetrieveSerializer
        return AlunoSerializer
