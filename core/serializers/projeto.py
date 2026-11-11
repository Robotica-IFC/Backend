from rest_framework.serializers import CharField, ModelSerializer, ReadOnlyField, SerializerMethodField

from core.models import Aluno, Professor, Projeto
from core.serializers.post import PostListRetrieveSerializer
from uploader.helpers.files import get_file_url
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    url = ReadOnlyField()

    class Meta:
        model = Image
        fields = ['attachment_key', 'url']


class ProfessorSimpleSerializer(ModelSerializer):
    nome = CharField(source='user.name', read_only=True, default=None)
    image_perfil = ImageSerializer(source='imagem_perfil', read_only=True)

    class Meta:
        model = Professor
        fields = ['id', 'nome', 'image_perfil']


class AlunoSimpleSerializer(ModelSerializer):
    nome = CharField(source='user.name', read_only=True, default=None)
    image_perfil = ImageSerializer(source='imagem_perfil', read_only=True)

    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'image_perfil']


class ProjetoSerializer(ModelSerializer):
    class Meta:
        model = Projeto
        fields = '__all__'


class ProjetoListSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    equipe = CharField(source='equipe.nome', read_only=True, default=None)
    instituicao = CharField(source='equipe.instituicao.nome', read_only=True, default=None)

    class Meta:
        model = Projeto
        fields = (
            'id',
            'titulo',
            'desc_curta',
            'equipe',
            'instituicao',
            'image_perfil',
            'status',
            'sugestao',
            'posts',
        )


class ProjetoDestaqueSerializer(ProjetoListSerializer):
    equipe_id = ReadOnlyField()
    equipe_views = ReadOnlyField(source='equipe.views')
    equipe_image = SerializerMethodField()

    class Meta(ProjetoListSerializer.Meta):
        fields = (
            'id', 'titulo', 'desc_curta', 'data_criacao', 'equipe', 'equipe_id',
            'equipe_views', 'equipe_image', 'image_perfil', 'status', 'sugestao',
        )

    def get_equipe_image(self, obj):
        if obj.equipe.image_perfil:
            return get_file_url(obj.equipe.image_perfil.file, self.context.get('request'))
        return None


class ProjetoRetrieveSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    equipe = CharField(source='equipe.nome', read_only=True, default=None)
    equipe_id = ReadOnlyField(source='equipe.id')
    equipe_image = SerializerMethodField()
    instituicao = CharField(source='equipe.instituicao.nome', read_only=True, default=None)
    posts = PostListRetrieveSerializer(many=True, read_only=True)

    professores = ProfessorSimpleSerializer(source='equipe.professores', many=True, read_only=True, default=[])
    alunos = AlunoSimpleSerializer(source='equipe.alunos', many=True, read_only=True, default=[])

    class Meta:
        model = Projeto
        fields = [
            'id',
            'titulo',
            'desc_curta',
            'descricao',
            'data_criacao',
            'status',
            'sugestao',
            'image_perfil',
            'equipe',
            'equipe_id',
            'equipe_image',
            'instituicao',
            'posts',
            'professores',
            'alunos',
        ]

    def get_equipe_image(self, obj):
        if obj.equipe and getattr(obj.equipe, 'image_perfil', None):
            image = obj.equipe.image_perfil
            if image and getattr(image, 'url', None):
                request = self.context.get('request')
                return request.build_absolute_uri(image.url) if request else image.url
        return None


class ProjetoDetailWithPostsSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    equipe = CharField(source='equipe.nome', read_only=True, default=None)
    equipe_id = ReadOnlyField(source='equipe.id')
    equipe_image = SerializerMethodField()
    instituicao = CharField(source='equipe.instituicao.nome', read_only=True, default=None)
    posts = PostListRetrieveSerializer(many=True, read_only=True)

    professores = ProfessorSimpleSerializer(source='equipe.professores', many=True, read_only=True, default=[])
    alunos = AlunoSimpleSerializer(source='equipe.alunos', many=True, read_only=True, default=[])

    class Meta:
        model = Projeto
        fields = [
            'id',
            'titulo',
            'desc_curta',
            'descricao',
            'data_criacao',
            'status',
            'sugestao',
            'image_perfil',
            'equipe',
            'equipe_id',
            'equipe_image',
            'instituicao',
            'posts',
            'professores',
            'alunos',
        ]

    def get_equipe_image(self, obj):
        if obj.equipe and getattr(obj.equipe, 'image_perfil', None):
            image = obj.equipe.image_perfil
            if image and getattr(image, 'url', None):
                request = self.context.get('request')
                return request.build_absolute_uri(image.url) if request else image.url
        return None
