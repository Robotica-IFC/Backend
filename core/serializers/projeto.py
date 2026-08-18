from rest_framework.serializers import CharField, ModelSerializer

from core.models import Projeto
from core.serializers.post import PostListRetrieveSerializer
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ['attachment_key', 'file']


class ProjetoSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Projeto
        fields = '__all__'


class ProjetoListSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    equipe = CharField(source="equipe.nome", read_only=True)
    instituicao = CharField(source="equipe.instituicao.nome", read_only=True)

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

    class Meta:
        model = Projeto
        fields = '__all__'
        depth = 3


class ProjetoDetailWithPostsSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    equipe = CharField(source="equipe.nome", read_only=True)
    equipe_id = CharField(source="equipe.id", read_only=True)
    instituicao = CharField(source="equipe.instituicao.nome", read_only=True)
    posts = PostListRetrieveSerializer(many=True, read_only=True)

    class Meta:
        model = Projeto
        fields = '__all__'
