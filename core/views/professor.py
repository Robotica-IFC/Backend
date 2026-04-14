from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from core.models import Professor
from core.serializers import ProfessorSerializer, ProfessorListSerializer, ProfessorRetrieveSerializer

class ProfessorViewSet(ModelViewSet):
    queryset = Professor.objects.all()
    serializer_class = ProfessorSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
       if self.action == 'list':
           return ProfessorListSerializer
       elif self.action == 'retrieve':
           return ProfessorRetrieveSerializer
       return ProfessorSerializer