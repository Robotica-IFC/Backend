from rest_framework import serializers
from rest_framework.serializers import ModelSerializer
from core.models import Convite


class ConviteSerializer(ModelSerializer):
    class Meta:
        model = Convite
        fields = '__all__'


class ConviteCreateSerializer(ModelSerializer):
    class Meta:
        model = Convite
        fields = ('id', 'equipe', 'aluno', 'professor', 'convidante', 'status')
        read_only_fields = ('status', 'convidante')

    def validate(self, attrs):
        aluno, professor, equipe = attrs.get('aluno'), attrs.get('professor'), attrs.get('equipe')
        if bool(aluno) == bool(professor):
            raise serializers.ValidationError('Escolha um aluno ou professor.')
        user = self.context['request'].user
        if not equipe.professores.filter(user=user).exists():
            raise serializers.ValidationError('Somente professores da equipe podem convidar.')
        if aluno and equipe.alunos.filter(pk=aluno.pk).exists():
            raise serializers.ValidationError('Aluno já faz parte da equipe.')
        if professor and equipe.professores.filter(pk=professor.pk).exists():
            raise serializers.ValidationError('Professor já faz parte da equipe.')
        if professor and professor.user_id == user.pk:
            raise serializers.ValidationError('Você não pode convidar a si mesmo.')
        if Convite.objects.filter(equipe=equipe, aluno=aluno, professor=professor, status='P').exists():
            raise serializers.ValidationError('Este usuário já tem um convite pendente.')
        return attrs

    def create(self, validated_data):
        validated_data['convidante'] = self.context['request'].user.professor_profile
        return super().create(validated_data)


class ConviteListRetrieveSerializer(ModelSerializer):
    equipe_nome = serializers.CharField(source='equipe.nome', read_only=True)
    convidante_nome = serializers.CharField(source='convidante.user.name', read_only=True)

    class Meta:
        model = Convite
        fields = ['id', 'equipe', 'equipe_nome', 'aluno', 'professor', 'convidante', 'convidante_nome', 'status']
