from rest_framework.serializers import (
    ModelSerializer,
    PrimaryKeyRelatedField,
    Serializer,
    SerializerMethodField,
    SlugRelatedField,
    ValidationError,
)

from core.models import Aluno, Equipe, Professor
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    class Meta:
        model = Image
        fields = ['attachment_key', 'file', 'url']


class EquipeSerializer(ModelSerializer):
    image_perfil = SlugRelatedField(
        slug_field='attachment_key',
        queryset=Image.objects.all(),
        required=False,
        allow_null=True
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
    estoque_id = PrimaryKeyRelatedField(source='estoque', read_only=True)
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


class SairEquipeSerializer(Serializer):
    def validate(self, attrs):
        user = self.context["request"].user
        equipe = self.context["equipe"]

        try:
            aluno = user.aluno_profile
        except Aluno.DoesNotExist:
            try:
                professor = user.professor_profile
            except Professor.DoesNotExist:
                raise ValidationError("Usuário não é aluno nem professor.")

            if not equipe.professores.filter(pk=professor.pk).exists():
                raise ValidationError("Professor não pertence a esta equipe.")

            if not equipe.professores.exclude(pk=professor.pk).exists():
                raise ValidationError("Professor é o único professor da equipe e não pode sair.")

            attrs["professor"] = professor
            return attrs

        if not equipe.alunos.filter(pk=aluno.pk).exists():
            raise ValidationError("Aluno não pertence a esta equipe.")

        attrs["aluno"] = aluno
        return attrs

    def create(self, validated_data):
        equipe = self.context["equipe"]

        if "aluno" in validated_data:
            equipe.alunos.remove(validated_data["aluno"])
        elif "professor" in validated_data:
            equipe.professores.remove(validated_data["professor"])

        return equipe
