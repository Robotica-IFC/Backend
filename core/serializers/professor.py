from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer, SlugRelatedField
from rest_framework import serializers

from core.models import Professor, User
from uploader.models import Image


class ProfessorSerializer(ModelSerializer):
    # Campos que pertencem ao USER, mas que o frontend envia no mesmo JSON
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
            "id", "name", "email", "username", "password", # Dados do User
            "cpf", "telefone", "data_nascimento", "imagem_perfil", 
            "instituicao", "ativo", "email_verificado", "is_professor"
        )

    def create(self, validated_data):
        # 1. Extraímos os dados do Usuário que estão no validated_data
        user_data = {
            "name": validated_data.pop("name"),
            "email": validated_data.pop("email"),
            "username": validated_data.pop("username"),
            "password": make_password(validated_data.pop("password")),
        }

        # 2. Criamos o Usuário primeiro
        user = User.objects.create(**user_data)

        # 3. Criamos o Professor associando-o ao usuário criado
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
