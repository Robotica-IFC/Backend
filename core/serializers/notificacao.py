from rest_framework import serializers

from core.models import Notificacao


class NotificacaoSerializer(serializers.ModelSerializer):
    projeto_titulo = serializers.CharField(source='projeto.titulo', read_only=True, default=None)
    equipe = serializers.SerializerMethodField()
    equipe_nome = serializers.SerializerMethodField()
    convite_status = serializers.CharField(source='convite.status', read_only=True, default=None)

    def get_equipe(self, obj):
        if obj.convite_id:
            return str(obj.convite.equipe_id)
        return str(obj.projeto.equipe_id) if obj.projeto_id else None

    def get_equipe_nome(self, obj):
        if obj.convite_id:
            return obj.convite.equipe.nome
        return obj.projeto.equipe.nome if obj.projeto_id else ''

    class Meta:
        model = Notificacao
        fields = ['id', 'tipo', 'titulo', 'mensagem', 'projeto', 'projeto_titulo',
                  'equipe', 'equipe_nome', 'post', 'convite', 'convite_status', 'criada_em', 'lida_em']
        read_only_fields = fields
