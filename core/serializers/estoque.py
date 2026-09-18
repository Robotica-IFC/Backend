from rest_framework import serializers

from core.models import Equipe, Estoque, Item
from uploader.models import Image
from uploader.serializers import ImageSerializer


class ItemSerializer(serializers.ModelSerializer):
    imagem_detail = ImageSerializer(source='imagem', read_only=True)

    class Meta:
        model = Item
        fields = ['id', 'nome', 'quantidade', 'descricao', 'imagem', 'imagem_detail', 'estoque']
        extra_kwargs = {
            'imagem': {'write_only': True},
            'estoque': {'required': True}
        }


class EstoqueSerializer(serializers.ModelSerializer):
    itens = ItemSerializer(many=True, read_only=True)
    equipe = serializers.PrimaryKeyRelatedField(queryset=Equipe.objects.all())

    class Meta:
        model = Estoque
        fields = ['id', 'equipe', 'itens']