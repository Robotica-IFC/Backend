import uuid
from django.db import models

from uploader.models import Image


class Equipe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    nome = models.CharField(max_length=50)
    descricao = models.CharField(max_length=1000, blank=True, null=True)
    ativo = models.BooleanField(default=True)

    image_perfil = models.ForeignKey(
        Image,
        related_name="+",
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    categorias = models.ManyToManyField(
        "core.Categoria",
        related_name="equipes",
        blank=True
    )


    professores = models.ManyToManyField(
        "core.Professor",
        related_name="equipes",
        blank=True
    )

    alunos = models.ManyToManyField(
        "core.Aluno",
        related_name="equipes",
        blank=True
    )

    instituicao = models.ForeignKey(
        "core.Instituicao",
        on_delete=models.CASCADE,
        related_name="equipes",
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.nome} - {self.instituicao}"

    class Meta:
        verbose_name = "equipe"
        verbose_name_plural = "equipes"