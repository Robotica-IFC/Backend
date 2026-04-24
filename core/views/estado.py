from rest_framework.viewsets import ModelViewSet

from core.models import Estado
from core.serializers import EstadoSerializer


class EstadoViewSet(ModelViewSet):
    queryset = Estado.objects.all()
    serializer_class = EstadoSerializer