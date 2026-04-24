import uuid

from django.db import models

from core.models import Estado
from uploader.models import Image


class Instituicao(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    sigla = models.CharField(max_length=20, null=True, blank=True)
    logo = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    cidade = models.CharField(max_length=255)
    estado = models.ForeignKey(Estado, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.nome} - {self.cidade}/{self.estado.sigla}'

    def save(self, *args, **kwargs):
        if self.sigla:
            self.sigla = self.sigla.upper()
        super().save(*args, **kwargs)
