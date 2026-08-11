from rest_framework.serializers import ModelSerializer, CharField

from core.models import Projeto
from core.views import instituicao
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
        )


class ProjetoRetrieveSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Projeto
        fields = '__all__'
        depth = 3