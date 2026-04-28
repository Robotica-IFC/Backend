from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from core.models import User


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'groups']
        depth = 1


class UserRegistrationSerializer(ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Campos base do User - ADICIONE O USERNAME AQUI
        token['name'] = user.name
        token['email'] = user.email
        token['username'] = user.username # <-- Faltava isso!

        # Lógica de perfis:
        if hasattr(user, 'aluno_profile'):
            aluno = user.aluno_profile
            token['tipo'] = 'aluno'
            token['cpf'] = aluno.cpf
            token['telefone'] = aluno.telefone   # <-- Faltava isso!
            token['descricao'] = aluno.descricao # <-- Faltava isso!
            token['imagem_perfil'] = str(aluno.imagem_perfil.attachment_key) if aluno.imagem_perfil else None

        elif hasattr(user, 'professor_profile'):
            professor = user.professor_profile
            token['tipo'] = 'professor'
            token['cpf'] = professor.cpf
            token['telefone'] = professor.telefone     # <-- Faltava isso!
            token['descricao'] = professor.descricao   # <-- Faltava isso!
            token['imagem_perfil'] = str(professor.imagem_perfil.attachment_key) if professor.imagem_perfil else None

        else:
            token['tipo'] = 'admin'

        return token
