from django.conf import settings
from django.db import models


class SolicitacaoEquipe(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'P', 'Pendente'
        ACEITA = 'A', 'Aceita'
        RECUSADA = 'R', 'Recusada'

    equipe = models.ForeignKey('core.Equipe', on_delete=models.CASCADE, related_name='solicitacoes')
    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solicitacoes_equipes')
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.PENDENTE)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['equipe', 'solicitante'], name='unique_solicitacao_equipe_usuario'),
        ]
        ordering = ['-criada_em']
