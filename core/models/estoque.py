from django.db import models

from uploader.models import Image


class Estoque(models.Model):
    equipe = models.OneToOneField(
        'core.equipe',
        on_delete=models.CASCADE,
        related_name='estoque',
        null=True,
        blank=True
    )

    def __str__(self):
        if self.equipe:
            return f'Estoque da equipe {self.equipe.nome}'
        return f'Estoque #{self.id} (Sem equipe)'


class Item(models.Model):
    estoque = models.ForeignKey(
        Estoque,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='itens'
    )
    nome = models.CharField(max_length=100)
    quantidade = models.PositiveIntegerField(default=0)
    descricao = models.TextField(blank=True, null=True)
    imagem = models.ForeignKey(
        Image,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='itens'
    )

    def __str__(self):
        return f'{self.nome} - {self.quantidade}'