# from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import Aluno, User
from uploader.models import Image


class AlunoSerializer(ModelSerializer):
    email = serializers.EmailField(write_only=True)
    name = serializers.CharField(write_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    # Adicione estes dois campos como write_only
    is_superuser = serializers.BooleanField(write_only=True, default=False)
    is_staff = serializers.BooleanField(write_only=True, default=False)

    imagem_perfil = SlugRelatedField(
        queryset=Image.objects.all(), slug_field='attachment_key', required=False, allow_null=True
    )

    class Meta:
        model = Aluno
        fields = [
            'id',
            'email',
            'name',
            'username',
            'password',
            'is_superuser',
            'is_staff',  # Inclua-os aqui
            'descricao',
            'cpf',
            'telefone',
            'data_nascimento',
            'imagem_perfil',
            'ativo',
            'email_verificado',
            'is_aluno',
            'user',
        ]
        depth = 1

    def create(self, validated_data):
        # Extrai os dados do usuário
        email = validated_data.pop('email')
        name = validated_data.pop('name')
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        # Extrai as flags de permissão
        is_superuser = validated_data.pop('is_superuser', False)
        is_staff = validated_data.pop('is_staff', False)

        # Cria o usuário com as permissões enviadas
        user = User.objects.create_user(
            email=email, name=name, username=username, password=password, is_superuser=is_superuser, is_staff=is_staff
        )

        aluno = Aluno.objects.create(user=user, **validated_data)
        return aluno


class AlunoListSerializer(ModelSerializer):
    class Meta:
        model = Aluno
        fields = '__all__'
        depth = 1


class AlunoRetrieveSerializer(ModelSerializer):
    class Meta:
        model = Aluno
        fields = '__all__'
        depth = 1
