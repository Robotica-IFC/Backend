from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from core.models import Professor
from core.serializers import ProfessorListSerializer, ProfessorRetrieveSerializer, ProfessorSerializer


class ProfessorViewSet(ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
       if self.action == 'list':  # noqa: E111
           return ProfessorListSerializer  # noqa: E111
       elif self.action == 'retrieve':  # noqa: E111
           return ProfessorRetrieveSerializer  # noqa: E111
       return ProfessorSerializer  # noqa: E111
