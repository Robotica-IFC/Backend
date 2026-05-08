import uuid

from django.db import models

from .equipe import Equipe


class Projeto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    concluido = models.BooleanField(default=False)
    equipe = models.ForeignKey(Equipe, related_name='equipes', on_delete=models.PROTECT)

    def __str__(self):
        return f'{self.nome} - {self.equipe.nome}'
