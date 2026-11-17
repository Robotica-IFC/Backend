from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.account_deletion import delete_account
from core.models import Aluno
from core.serializers import AlunoListSerializer, AlunoRetrieveSerializer, AlunoSerializer


class AlunoViewSet(ModelViewSet):
    queryset = Aluno.objects.all()
    filter_backends = [SearchFilter]
    search_fields = ['user__name', 'user__username']
    serializer_class = AlunoSerializer
    permission_classes = [AllowAny]  # permite a criação de usuarios por qualquer usuario

    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAuthenticated()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        aluno = self.get_object()
        if aluno.user_id != request.user.pk:
            raise PermissionDenied('Você só pode excluir sua própria conta.')
        delete_account(aluno.user_id)
        return Response(status=204)

    def get_serializer_class(self):
        if self.action == 'list':
            return AlunoListSerializer
        elif self.action == 'retrieve':
            return AlunoRetrieveSerializer
        return AlunoSerializer
