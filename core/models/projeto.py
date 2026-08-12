from django.db import models

from uploader.models import Image

from .equipe import Equipe


class Projeto(models.Model):
    class Status(models.TextChoices):
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        CONCLUIDO = "CONCLUIDO", "Concluído"
        CANCELADO = "CANCELADO", "Cancelado"

    titulo = models.CharField(max_length=20)
    desc_curta = models.CharField(max_length=60)
    descricao = models.TextField()
    data_criacao = models.DateField(auto_now_add=True)
    sugestao = models.BooleanField(default=True)

    image_perfil = models.ForeignKey(
        Image,
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    equipe = models.ForeignKey(
        Equipe,
        on_delete=models.CASCADE,
        related_name='projetos'
        )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.EM_ANDAMENTO
    )

    def __str__(self):
        return f'{self.titulo} - {self.equipe} - {self.get_status_display()}'

    class Meta:
<<<<<<< HEAD
        verbose_name = "projeto"
=======
        verbose_name= "projeto"
>>>>>>> 00995e4759522ff1301f360a2355abcaa881ec19
        verbose_name_plural = "projetos"
