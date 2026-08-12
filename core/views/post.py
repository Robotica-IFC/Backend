from rest_framework import permissions, viewsets

from core.models import Post
from core.serializers import PostCreateSerializer, PostListRetrieveSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-criado_em')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return PostCreateSerializer

        return PostListRetrieveSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action in {'list', 'retrieve'}:
            queryset = queryset.select_related(
                'aluno_criador',
                'professor_criador'
            ).prefetch_related('images')

        return queryset
