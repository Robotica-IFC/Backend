from django.contrib.auth.hashers import make_password
from rest_framework.serializers import ModelSerializer

from core.models import Aluno


class AlunoSerializer(ModelSerializer):

    class Meta:
        model = Aluno
        fields = "__all__"
        # extra_kwargs = {
        #     "senha": {"write_only": True}  # impede a exibição da senha
        # }

    def create(self, validated_data):  # criptografa a senha ASS: Lucas
        validated_data["senha"] = make_password(validated_data["senha"])
        return super().create(validated_data)
