from rest_framework import serializers

from core.models import Equipe, SugestaoProjeto, User
from uploader.helpers.files import get_file_url
from uploader.models import Document
from uploader.serializers.document import DocumentSerializer

MAX_SUGGESTION_ATTACHMENTS = 4


class SugestaoProjetoSerializer(serializers.ModelSerializer):
    favorita = serializers.BooleanField(read_only=True, default=False)
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
        fields = [
            'id', 'titulo', 'equipe', 'descricao', 'anonimo', 'autor', 'anexos', 'criado_em',
            'recusada', 'recusada_em', 'favorita',
        ]
        read_only_fields = ['id', 'autor', 'criado_em', 'recusada', 'recusada_em']

    def validate_anexos(self, value):
        if len(value) > MAX_SUGGESTION_ATTACHMENTS:
            raise serializers.ValidationError('Envie no máximo 4 anexos por sugestão.')
        return value

    def create(self, validated_data):
        validated_data['autor'] = None if validated_data['anonimo'] else self.context['request'].user
        return super().create(validated_data)


class SugestaoProjetoAutorSerializer(serializers.ModelSerializer):
    perfil_id = serializers.SerializerMethodField()
    tipo = serializers.SerializerMethodField()
    imagem_perfil = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'username', 'perfil_id', 'tipo', 'imagem_perfil']

    def get_profile(self, obj):
        return getattr(obj, 'aluno_profile', None) or getattr(obj, 'professor_profile', None)

    def get_perfil_id(self, obj):
        profile = self.get_profile(obj)
        return str(profile.pk) if profile else None

    def get_tipo(self, obj):
        if getattr(obj, 'aluno_profile', None):
            return 'aluno'
        if getattr(obj, 'professor_profile', None):
            return 'professor'
        return None

    def get_imagem_perfil(self, obj):
        profile = self.get_profile(obj)
        if not profile or not profile.imagem_perfil:
            return None
        return {'url': get_file_url(profile.imagem_perfil.file, self.context.get('request'))}


class SugestaoProjetoListRetrieveSerializer(serializers.ModelSerializer):
    favorita = serializers.BooleanField(read_only=True, default=False)
    equipe_nome = serializers.ReadOnlyField(source='equipe.nome')
    autor = serializers.SerializerMethodField()
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
            'recusada',
            'recusada_em',
            'favorita',
        ]

    def get_autor(self, obj):
        if obj.anonimo or not obj.autor:
            return None
        return SugestaoProjetoAutorSerializer(obj.autor, context=self.context).data
