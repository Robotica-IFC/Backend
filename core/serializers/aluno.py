from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer, SlugRelatedField
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers

from core.models import Aluno, User
from uploader.models import Image


class AlunoSerializer(ModelSerializer):
    # Campos que pertencem ao USER, mas que o frontend envia no formulário de ALUNO
    email = serializers.EmailField(source='user.email')
    name = serializers.CharField(source='user.name')
    username = serializers.CharField(source='user.username') 
    password = serializers.CharField(write_only=True)

    imagem_perfil = SlugRelatedField(
        queryset=Image.objects.all(),
        slug_field='attachment_key',
        required=False,
        allow_null=True
    )

    class Meta:
        model = Aluno
        # Adicione os campos do User aqui também para que o Serializer os aceite
        fields = ["id", "email", "name", "username", "password", "descricao", "cpf", "telefone", "data_nascimento", "imagem_perfil"]

    def create(self, validated_data):
        # 1. Separar os dados do User dos dados do Aluno
        user_data = validated_data.pop('user')
        password = validated_data.pop('password')

        # 2. Criar o User usando o Manager (que cuida da criptografia da senha)
        user = User.objects.create_user(
            email=user_data['email'],
            name=user_data['name'],
            username=user_data['username'],
            password=password
        )

        # 3. Criar o Aluno associado a esse User
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


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['name'] = user.name
        token['email'] = user.email
        token['username'] = user.username

        # MUDANÇA: Usar aluno_profile pois é o que está no seu models.py
        if hasattr(user, 'aluno_profile'): 
            aluno = user.aluno_profile
            token['tipo'] = 'aluno'
            token['cpf'] = aluno.cpf
            token['telefone'] = aluno.telefone
            token['descricao'] = aluno.descricao
            
            if aluno.imagem_perfil:
                token['imagem_perfil'] = str(aluno.imagem_perfil.attachment_key)
            else:
                token['imagem_perfil'] = None
        else:
            token['tipo'] = 'professor'
        
        return token