from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import Aluno
from uploader.models import Image


class AlunoSerializer(ModelSerializer):

    imagem_perfil = SlugRelatedField(
        queryset=Image.objects.all(),
        slug_field='attachment_key',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Aluno
        fields = "__all__"
        # extra_kwargs = {
        #     "senha": {"write_only": True}  # impede a exibição da senha
        # }

    def create(self, validated_data):  # criptografa a senha ASS: Lucas
        validated_data["senha"] = make_password(validated_data["senha"])
        return super().create(validated_data)


class AlunoListSerializer(ModelSerializer):
    class Meta:
        model = Aluno
        fields = '__all__'
        depth = 1


class AlunoRetrieveSerializer(ModelSerializer):
    class Meta:
        model = Aluno
        fields = 'attachment_key', 'file'
        depth = 1
