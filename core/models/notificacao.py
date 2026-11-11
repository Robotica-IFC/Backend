from django.conf import settings
from django.db import models


class Notificacao(models.Model):
    class Tipo(models.TextChoices):
        PROJETO = 'PROJETO', 'Novo projeto'
        POST = 'POST', 'Novo post'

    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notificacoes',
    )
    projeto = models.ForeignKey('core.Projeto', on_delete=models.CASCADE, related_name='notificacoes')
    post = models.ForeignKey(
        'core.Post', on_delete=models.SET_NULL, null=True, blank=True, related_name='notificacoes',
    )
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    titulo = models.CharField(max_length=100)
    mensagem = models.TextField()
    criada_em = models.DateTimeField(auto_now_add=True)
    lida_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-criada_em', '-id']
        indexes = [models.Index(fields=['destinatario', 'lida_em'], name='notificacao_dest_lida_idx')]

