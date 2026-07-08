from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import Equipe
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ['attachment_key', 'file']


class EquipeSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Equipe
        fields = '__all__'


class EquipeListRetrieveSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Equipe
        fields = '__all__'
        depth = 2


class EquipeCardSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Equipe
        fields = ['id', 'nome', 'image_perfil']

