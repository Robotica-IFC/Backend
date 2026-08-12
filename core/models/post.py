from django.db import models

from uploader.models import Image


class Post(models.Model):
    legenda = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    aluno_criador = models.ForeignKey(
        'core.Aluno',
        related_name='posts',
        on_delete=models.PROTECT,
        null=True,
        blank=True
        )
    professor_criador = models.ForeignKey(
        'core.Professor',
        related_name='posts',
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )
    projeto = models.ForeignKey(
        'core.Projeto',
        on_delete=models.CASCADE,
        related_name='posts',
        null=True,
        blank=True
    )


class PostImage(models.Model):
    post = models.ForeignKey(
        Post,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ForeignKey(
        Image,
        related_name="+",
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
