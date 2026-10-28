from rest_framework import serializers

from core.models import Equipe, SugestaoProjeto, User
from uploader.models import Document
from uploader.serializers.document import DocumentSerializer


class SugestaoProjetoSerializer(serializers.ModelSerializer):
    equipe = serializers.PrimaryKeyRelatedField(queryset=Equipe.objects.filter(ativo=True))
    anonimo = serializers.BooleanField(default=True)
    anexos = serializers.SlugRelatedField(
        slug_field='attachment_key',
        queryset=Document.objects.all(),
        many=True,
        required=False,
    )

    class Meta:
        model = SugestaoProjeto
        fields = ['id', 'titulo', 'equipe', 'descricao', 'anonimo', 'autor', 'anexos', 'criado_em']
        read_only_fields = ['id', 'autor', 'criado_em']

    def create(self, validated_data):
        validated_data['autor'] = None if validated_data['anonimo'] else self.context['request'].user
        return super().create(validated_data)


class SugestaoProjetoAutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'username']


class SugestaoProjetoListRetrieveSerializer(serializers.ModelSerializer):
    equipe_nome = serializers.ReadOnlyField(source='equipe.nome')
    autor = SugestaoProjetoAutorSerializer(read_only=True)
    anexos = DocumentSerializer(many=True, read_only=True)

    class Meta:
        model = SugestaoProjeto
        fields = [
            'id',
            'titulo',
            'equipe',
            'equipe_nome',
            'descricao',
            'anonimo',
            'autor',
            'anexos',
            'criado_em',
        ]
