from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SlugRelatedField

from core.models import Professor, User
from uploader.models import Image


class ProfessorSerializer(ModelSerializer):
    name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    imagem_perfil = SlugRelatedField(
        queryset=Image.objects.all(),
        slug_field='attachment_key',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Professor
        fields = (
            "id", "name", "email", "username", "password",
            "cpf", "telefone", "data_nascimento", "imagem_perfil",
            "instituicao", "ativo", "email_verificado", "is_professor",
            "user", "descricao"
        )

    def create(self, validated_data):
        name = validated_data.pop("name")
        email = validated_data.pop("email")
        username = validated_data.pop("username")
        password = validated_data.pop("password")

        user = User.objects.create_user(
            email=email,
            name=name,
            username=username,
            password=password
        )

        professor = Professor.objects.create(user=user, **validated_data)
        return professor


class ProfessorListSerializer(ModelSerializer):
    class Meta:
        model = Professor
        fields = '__all__'
        depth = 2


class ProfessorRetrieveSerializer(ModelSerializer):
    class Meta:
        model = Professor
        fields = '__all__'
        depth = 2
