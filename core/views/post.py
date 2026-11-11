from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.models import Post, PostLike, PostComment
from core.permissions_social import CanEditPost, is_team_member
from core.serializers import PostCreateSerializer, PostListRetrieveSerializer
from core.serializers.post import PostCommentSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-criado_em')
    permission_classes = [permissions.IsAuthenticated, CanEditPost]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action in {'create', 'update', 'partial_update'}:
            return PostCreateSerializer
        return PostListRetrieveSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in {'list', 'retrieve'}:
            queryset = queryset.select_related(
                'aluno_criador__user', 'professor_criador__user'
            ).prefetch_related('images__image', 'comments__user', 'likes')
        return queryset

    def perform_create(self, serializer):
        projeto = serializer.validated_data.get('projeto')
        if not projeto or not is_team_member(self.request.user, projeto.equipe):
            raise PermissionDenied('Apenas membros da equipe podem publicar.')
        serializer.save()

    def perform_update(self, serializer):
        projeto = serializer.validated_data.get('projeto')
        if projeto and projeto.pk != serializer.instance.projeto_id:
            raise ValidationError({'projeto': 'Não é permitido mover o post para outro projeto.'})
        serializer.save()

    @action(detail=True, methods=['post', 'delete'], url_path='curtir')
    def curtir(self, request, pk=None):
        post = self.get_object()
        if request.method == 'POST':
            PostLike.objects.get_or_create(post=post, user=request.user)
        else:
            PostLike.objects.filter(post=post, user=request.user).delete()
        return Response({'curtidas': post.likes.count(), 'curtiu': request.method == 'POST'})

    @action(detail=True, methods=['get', 'post'], url_path='comentarios')
    def comentarios(self, request, pk=None):
        post = self.get_object()
        if request.method == 'GET':
            return Response(PostCommentSerializer(post.comments.select_related('user'), many=True).data)
        texto = str(request.data.get('texto', '')).strip()
        if not texto or len(texto) > 1000:
            raise ValidationError({'texto': 'Informe um comentário de até 1000 caracteres.'})
        comentario = PostComment.objects.create(post=post, user=request.user, texto=texto)
        return Response(PostCommentSerializer(comentario).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'comentarios/(?P<comentario_id>[^/.]+)')
    def excluir_comentario(self, request, pk=None, comentario_id=None):
        post = self.get_object()
        comentario = post.comments.filter(pk=comentario_id).first()
        if not comentario:
            from rest_framework.exceptions import NotFound
            raise NotFound('Comentário não encontrado.')
        if comentario.user_id != request.user.pk and not request.user.is_staff:
            raise PermissionDenied('Apenas o autor pode excluir o comentário.')
        comentario.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
