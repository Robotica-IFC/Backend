from rest_framework import serializers

from core.models import Equipe, Estoque, Item
from uploader.serializers import ImageSerializer


class ItemSerializer(serializers.ModelSerializer):
    imagem_detail = ImageSerializer(source='imagem', read_only=True)
    categoria_display = serializers.CharField(
        source='get_categoria_display',
        read_only=True
    )

    class Meta:
        model = Item
        fields = [
            'id',
            'nome',
            'quantidade',
            'descricao',
            'categoria',
            'categoria_display',
            'imagem',
            'imagem_detail',
            'estoque'
        ]
        extra_kwargs = {
            'imagem': {'write_only': True},
            'estoque': {'required': True}
        }


class InstituicaoResumidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Equipe._meta.get_field('instituicao').related_model
        fields = ['id', 'sigla', 'cidade', 'estado']


class EquipeResumidaSerializer(serializers.ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    instituicao = InstituicaoResumidaSerializer(read_only=True)

    class Meta:
        model = Equipe
        fields = ['id', 'nome', 'image_perfil', 'instituicao']


class EstoqueSerializer(serializers.ModelSerializer):
    itens = ItemSerializer(many=True, read_only=True)
    equipe = serializers.PrimaryKeyRelatedField(queryset=Equipe.objects.all())

    class Meta:
        model = Estoque
        fields = ['id', 'equipe', 'itens']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.equipe:
            representation['equipe'] = EquipeResumidaSerializer(instance.equipe).data
        return representation