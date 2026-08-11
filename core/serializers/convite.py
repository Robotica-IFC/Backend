from pyexpat import model

from rest_framework.serializers import ModelSerializer
from rest_framework import serializers

from core.models import Convite


class ConviteSerializer(ModelSerializer):
    class Meta:
        model = Convite
        fields = '__all__'


class ConviteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Convite
        fields = ('id', 'equipe', 'aluno', 'professor', 'convidante', 'status')
        # convidante e status devem ser gerenciados pelo sistema, não informados no JSON de envio
        read_only_fields = ('status', 'convidante')

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
        depth = 3
