from rest_framework.viewsets import ModelViewSet

from core.models import Instituicao
from core.serializers import InstituicaoSerializer


class InstituicaoViewSet(ModelViewSet):
    queryset = Instituicao.objects.all()
    serializer_class = InstituicaoSerializer