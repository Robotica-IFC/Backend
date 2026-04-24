from rest_framework.viewsets import ModelViewSet

from core.models import Instituicao
from core.serializers import InstituicaoListRetrieveSerializer, InstituicaoSerializer


class InstituicaoViewSet(ModelViewSet):
    queryset = Instituicao.objects.all()
    serializer_class = InstituicaoSerializer

    def get_serializer_class(self):
       if self.action == 'list':  # noqa: E111
           return InstituicaoListRetrieveSerializer  # noqa: E111
       elif self.action == 'retrieve':  # noqa: E111
           return InstituicaoListRetrieveSerializer  # noqa: E111
       return InstituicaoSerializer  # noqa: E111
