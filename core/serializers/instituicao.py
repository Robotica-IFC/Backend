from rest_framework.serializers import ModelSerializer, ReadOnlyField

from core.models import Instituicao
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    url = ReadOnlyField()

    class Meta:
        model = Image
        fields = ['attachment_key', 'url']


class InstituicaoSerializer(ModelSerializer):
    class Meta:
        model = Instituicao
        fields = '__all__'


class InstituicaoListRetrieveSerializer(ModelSerializer):
    logo = ImageSerializer(read_only=True)

    class Meta:
        model = Instituicao
        fields = ['id', 'nome', 'sigla', 'cidade', 'estado', 'logo']
