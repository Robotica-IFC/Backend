from rest_framework import serializers

from core.models import Convite

class ConviteSerializer(serializers.ModelSerializer):
    nomeTime = serializers.CharField(source="equipe.nome", read_only=True)
    convitePorNome = serializers.CharField(source="enviadosPor.name", read_only=True)

    class Meta:
        model = Convite
        fields = [
            "id", "equipe", "nomeTime","convitePorNome", "status", "criacao", "resposta"
        ]
        read_only_fields = fields


class CreateConviteSerializer(serializers.Serializer):
    alunoId = serializers.IntegerField()

class ConfirmConviteSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6) 