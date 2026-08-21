
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from core.models import Convite


class ConviteSerializer(ModelSerializer):
    class Meta:
        model = Convite
        fields = '__all__'


class ConviteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Convite
        fields = ("id", "equipe", "aluno", "professor", "convidante", "status")
        read_only_fields = ("status", "convidante")

    def create(self, validated_data):
        user = self.context["request"].user

        # Tenta pegar pelo related_name customizado
        try:
            professor_instance = user.professor_profile
        except AttributeError:
            # Caso o atributo não exista ou o user não tenha perfil de professor criado
            raise serializers.ValidationError(
                {
                    "convidante": (
                        f"O usuário {user.email} não possui um perfil de"
                        " Professor cadastrado."
                    )
                }
            )

        validated_data["convidante"] = professor_instance
        return super().create(validated_data)

    def validate(self, attrs):
        aluno = attrs.get('aluno')
        professor = attrs.get('professor')

        if aluno and professor:
            raise serializers.ValidationError(
                "O convite deve ser enviado para um Aluno OU um Professor, nunca para ambos."
            )

        if not aluno and not professor:
            raise serializers.ValidationError(
                "Você precisa informar um Aluno ou um Professor para receber o convite."
            )

        return attrs


class ConviteListRetrieveSerializer(ModelSerializer):
    class Meta:
        model = Convite
        fields = '__all__'
        depth = 1
