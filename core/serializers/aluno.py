from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import Aluno, User
from uploader.models import Image


class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'username', 'is_active', 'is_staff', 'last_login']


class AlunoSerializer(ModelSerializer):
    email = serializers.EmailField(write_only=True)
    name = serializers.CharField(write_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    imagem_perfil = SlugRelatedField(
        queryset=Image.objects.all(),
        slug_field='attachment_key',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Aluno
        fields = [
            "id", "email", "name", "username", "password",
            "descricao", "cpf", "telefone", "data_nascimento",
            "imagem_perfil", "ativo", "email_verificado", "is_aluno", 'user'
        ]
        depth = 1

    def create(self, validated_data):
        email = validated_data.pop('email')
        name = validated_data.pop('name')
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            email=email,
            name=name,
            username=username,
            password=password
        )

        aluno = Aluno.objects.create(user=user, **validated_data)
        return aluno


class AlunoListSerializer(ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Aluno
        fields = [
            "id", "user", "descricao", "cpf", "telefone", 
            "data_nascimento", "imagem_perfil", "ativo", 
            "email_verificado", "is_aluno"
        ]
        depth = 1


class AlunoRetrieveSerializer(ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model = Aluno
        fields = [
            "id", "user", "descricao", "cpf", "telefone", 
            "data_nascimento", "imagem_perfil", "ativo", 
            "email_verificado", "is_aluno"
        ]
        depth = 1
