from rest_framework.serializers import (
    ModelSerializer,
    ReadOnlyField,
    Serializer,
    SerializerMethodField,
    SlugRelatedField,
    ValidationError,
)

from core.models import Aluno, Categoria, Equipe, Instituicao, Professor, User
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    url = ReadOnlyField()

    class Meta:
        model = Image
        fields = ['attachment_key', 'url']


class InstituicaoCardSerializer(ModelSerializer):
    class Meta:
        model = Instituicao
        fields = ['id', 'sigla', 'nome', 'cidade', 'estado']


class UserPublicSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'username']


class ProfessorEquipeSerializer(ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    imagem_perfil = ImageSerializer(read_only=True)
    instituicao = InstituicaoCardSerializer(read_only=True)

    class Meta:
        model = Professor
        fields = ['id', 'user', 'imagem_perfil', 'instituicao']


class AlunoEquipeSerializer(ModelSerializer):
    user = UserPublicSerializer(read_only=True)
    imagem_perfil = ImageSerializer(read_only=True)

    class Meta:
        model = Aluno
        fields = ['id', 'user', 'imagem_perfil']


class ProfessorCardSerializer(ModelSerializer):
    username = ReadOnlyField(source='user.username')

    class Meta:
        model = Professor
        fields = ['id', 'username']


class CategoriaCardSerializer(ModelSerializer):
    class Meta:
        model = Categoria
        fields = ['id', 'nome']


class EquipeSerializer(ModelSerializer):
    image_perfil = SlugRelatedField(
        slug_field='attachment_key', queryset=Image.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Equipe
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image_perfil:
            representation['image_perfil'] = ImageSerializer(instance.image_perfil).data
        return representation


class EquipeListRetrieveSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    professores = ProfessorEquipeSerializer(many=True, read_only=True)
    alunos = AlunoEquipeSerializer(many=True, read_only=True)
    categorias = CategoriaCardSerializer(many=True, read_only=True)
    instituicao = InstituicaoCardSerializer(read_only=True)
    total_projetos = SerializerMethodField()
    estoque_id = SerializerMethodField()

    def get_total_projetos(self, obj):
        return obj.projetos.count()

    def get_estoque_id(self, obj):
        estoque = getattr(obj, 'estoque', None)
        return estoque.id if estoque else None

    class Meta:
        model = Equipe
        fields = [
            'id',
            'nome',
            'descricao',
            'ativo',
            'views',
            'image_perfil',
            'professores',
            'alunos',
            'categorias',
            'instituicao',
            'total_projetos',
            'estoque_id',
        ]


class EquipeCardSerializer(ModelSerializer):
    image_perfil = ImageSerializer(read_only=True)
    professores = ProfessorCardSerializer(many=True, read_only=True)
    categorias = CategoriaCardSerializer(many=True, read_only=True)
    instituicao = InstituicaoCardSerializer(read_only=True)
    total_projetos = SerializerMethodField()

    def get_total_projetos(self, obj):
        return obj.projetos.count()

    class Meta:
        model = Equipe
        fields = [
            'id',
            'nome',
            'image_perfil',
            'professores',
            'categorias',
            'instituicao',
            'total_projetos',
        ]


class SairEquipeSerializer(Serializer):
    def validate(self, attrs):
        user = self.context['request'].user
        equipe = self.context['equipe']

        try:
            aluno = user.aluno_profile
        except Aluno.DoesNotExist:
            try:
                professor = user.professor_profile
            except Professor.DoesNotExist:
                raise ValidationError('Usuário não é aluno nem professor.')

            if not equipe.professores.filter(pk=professor.pk).exists():
                raise ValidationError('Professor não pertence a esta equipe.')

            if not equipe.professores.exclude(pk=professor.pk).exists():
                raise ValidationError('Professor é o único professor da equipe e não pode sair.')

            attrs['professor'] = professor
            return attrs

        if not equipe.alunos.filter(pk=aluno.pk).exists():
            raise ValidationError('Aluno não pertence a esta equipe.')

        attrs['aluno'] = aluno
        return attrs

    def create(self, validated_data):
        equipe = self.context['equipe']

        if 'aluno' in validated_data:
            equipe.alunos.remove(validated_data['aluno'])
        elif 'professor' in validated_data:
            equipe.professores.remove(validated_data['professor'])

        return equipe
