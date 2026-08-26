from rest_framework.serializers import ModelSerializer, SerializerMethodField, SlugRelatedField

from core.models import Equipe
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ['attachment_key', 'file', 'url']


class EquipeSerializer(ModelSerializer):
    # Permite ESCREVER enviando apenas a string da attachment_key e LER retornando a chave
    image_perfil = SlugRelatedField(
        slug_field='attachment_key',
        queryset=Image.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Equipe
        fields = '__all__'

    # Sobrescreve to_representation para RETORNAR a imagem serializada completa no GET
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image_perfil:
            representation['image_perfil'] = ImageSerializer(instance.image_perfil).data
        return representation


class EquipeListRetrieveSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    total_projetos = SerializerMethodField()

    def get_total_projetos(self, obj):
        return obj.projetos.count()

    class Meta:
        model = Equipe
        fields = '__all__'
        depth = 2


class EquipeCardSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Equipe
        fields = ['id', 'nome', 'image_perfil']
