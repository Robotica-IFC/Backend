from rest_framework import serializers

from core.models import Notificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    projeto_titulo = serializers.CharField(source='projeto.titulo', read_only=True)
    equipe_nome = serializers.CharField(source='projeto.equipe.nome', read_only=True)

    class Meta:
        model = Notificacao
        fields = ['id', 'tipo', 'titulo', 'mensagem', 'projeto', 'projeto_titulo',
                  'equipe_nome', 'post', 'criada_em', 'lida_em']
        read_only_fields = fields
