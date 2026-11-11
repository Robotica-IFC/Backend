from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from core.account_deletion import delete_account
from core.models import Professor
from core.serializers import ProfessorListSerializer, ProfessorRetrieveSerializer, ProfessorSerializer


class ProfessorViewSet(ModelViewSet):
    queryset = Professor.objects.all()
    filter_backends = [SearchFilter]
    search_fields = ['user__name', 'user__username']
    serializer_class = ProfessorSerializer
    permission_classes = [AllowAny]

    http_method_names = ['get', 'post', 'put', 'delete', 'patch']

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAuthenticated()]
        return super().get_permissions()

    def destroy(self, request, *args, **kwargs):
        professor = self.get_object()
        if professor.user_id != request.user.pk:
            raise PermissionDenied('Você só pode excluir sua própria conta.')
        delete_account(professor.user_id)
        return Response(status=204)

    def get_serializer_class(self):
       if self.action == 'list':  # noqa: E111
           return ProfessorListSerializer  # noqa: E111
       elif self.action == 'retrieve':  # noqa: E111
           return ProfessorRetrieveSerializer  # noqa: E111
       return ProfessorSerializer  # noqa: E111
