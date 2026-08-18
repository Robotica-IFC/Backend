from rest_framework import serializers
from rest_framework.serializers import CharField, ModelSerializer, ReadOnlyField, SerializerMethodField

from core.models import Aluno, Professor, Projeto
from core.serializers.post import PostListRetrieveSerializer
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ['attachment_key', 'file']


class ProfessorSimpleSerializer(ModelSerializer):
    nome = CharField(source="user.name", read_only=True, default=None)
    image_perfil = ImageSerializer(source="imagem_perfil", read_only=True)

    class Meta:
        model = Professor
        fields = ['id', 'nome', 'image_perfil']


class AlunoSimpleSerializer(ModelSerializer):
    nome = CharField(source="user.name", read_only=True, default=None)
    image_perfil = ImageSerializer(source="imagem_perfil", read_only=True)

    class Meta:
        model = Aluno
        fields = ['id', 'nome', 'image_perfil']


class ProjetoSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Projeto
        fields = '__all__'


class ProjetoListSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    equipe = CharField(source="equipe.nome", read_only=True, default=None)
    instituicao = CharField(source="equipe.instituicao.nome", read_only=True, default=None)

    class Meta:
        model = Projeto
        fields = (
            "id",
            "titulo",
            "desc_curta",
            "equipe",
            "instituicao",
            "image_perfil",
            "status",
            "posts",
        )


class ProjetoRetrieveSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    equipe = CharField(source="equipe.nome", read_only=True, default=None)
    equipe_id = ReadOnlyField(source="equipe.id")
    equipe_image = SerializerMethodField()
    instituicao = CharField(source="equipe.instituicao.nome", read_only=True, default=None)
    posts = PostListRetrieveSerializer(many=True, read_only=True)

    professores = ProfessorSimpleSerializer(
        source="equipe.professores",
        many=True,
        read_only=True,
        default=[]
    )
    alunos = AlunoSimpleSerializer(
        source="equipe.alunos",
        many=True,
        read_only=True,
        default=[]
    )

    class Meta:
        model = Projeto
        fields = '__all__'

    def get_equipe_image(self, obj):
        if obj.equipe and getattr(obj.equipe, 'image_perfil', None):
            image = obj.equipe.image_perfil
            if hasattr(image, 'file') and image.file:
                request = self.context.get('request')
                return request.build_absolute_uri(image.file.url) if request else image.file.url
        return None


class ProjetoDetailWithPostsSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    equipe = CharField(source="equipe.nome", read_only=True, default=None)
    equipe_id = ReadOnlyField(source="equipe.id")
    equipe_image = SerializerMethodField()
    instituicao = CharField(source="equipe.instituicao.nome", read_only=True, default=None)
    posts = PostListRetrieveSerializer(many=True, read_only=True)

    professores = ProfessorSimpleSerializer(
        source="equipe.professores",
        many=True,
        read_only=True,
        default=[]
    )
    alunos = AlunoSimpleSerializer(
        source="equipe.alunos",
        many=True,
        read_only=True,
        default=[]
    )

    class Meta:
        model = Projeto
        fields = '__all__'

    def get_equipe_image(self, obj):
        if obj.equipe and getattr(obj.equipe, 'image_perfil', None):
            image = obj.equipe.image_perfil
            if hasattr(image, 'file') and image.file:
                request = self.context.get('request')
                return request.build_absolute_uri(image.file.url) if request else image.file.url
        return None
