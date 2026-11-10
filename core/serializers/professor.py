from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.email_verification import send_initial_code
from core.models import Professor, User
from uploader.models import Image


class ImageSerializer(ModelSerializer):
    url = serializers.ReadOnlyField()

    class Meta:
        model = Image
        fields = ['attachment_key', 'url']


class InstituicaoMiniSerializer(ModelSerializer):
    class Meta:
        model = Professor._meta.get_field('instituicao').related_model
        fields = ['id', 'nome', 'sigla', 'cidade', 'estado']


class UserProfileSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'username']


class ProfessorSerializer(ModelSerializer):
    name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    imagem_perfil = SlugRelatedField(
        queryset=Image.objects.all(), slug_field='attachment_key', required=False, allow_null=True
    )

    class Meta:
        model = Professor
        fields = (
            'id',
            'name',
            'email',
            'username',
            'password',
            'cpf',
            'telefone',
            'data_nascimento',
            'imagem_perfil',
            'instituicao',
            'ativo',
            'email_verificado',
            'is_professor',
            'user',
            'descricao',
        )
        read_only_fields = ['user', 'email_verificado']

    def create(self, validated_data):
        name = validated_data.pop('name')
        email = validated_data.pop('email')
        username = validated_data.pop('username')
        password = validated_data.pop('password')

        with transaction.atomic():
            user = User.objects.create_user(email=email, name=name, username=username, password=password)

            professor = Professor.objects.create(user=user, **validated_data)
            transaction.on_commit(lambda: send_initial_code(user))
            return professor


class ProfessorListSerializer(ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    imagem_perfil = ImageSerializer(read_only=True)
    instituicao = InstituicaoMiniSerializer(read_only=True)

    class Meta:
        model = Professor
        fields = [
            'id',
            'user',
            'cpf',
            'telefone',
            'data_nascimento',
            'imagem_perfil',
            'instituicao',
            'ativo',
            'email_verificado',
            'is_professor',
            'descricao',
        ]


class ProfessorRetrieveSerializer(ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    imagem_perfil = ImageSerializer(read_only=True)
    instituicao = InstituicaoMiniSerializer(read_only=True)

    class Meta:
        model = Professor
        fields = [
            'id',
            'user',
            'cpf',
            'telefone',
            'data_nascimento',
            'imagem_perfil',
            'instituicao',
            'ativo',
            'email_verificado',
            'is_professor',
            'descricao',
        ]
