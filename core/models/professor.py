import uuid

from django.db import models

from uploader.models import Image


class Professor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    cpf = models.CharField(max_length=11, unique=True)
    senha = models.CharField(max_length=400)
    telefone = models.CharField(max_length=15)
    data_nascimento = models.DateField()
    instituicao = models.CharField(max_length=300)
    ativo = models.BooleanField(default=True)
    email_verificado = models.BooleanField(default=False)
    imagem_perfil = models.ForeignKey(Image, to_field='attachment_key', related_name='+', on_delete=models.SET_NULL, null=True, blank=True)  # noqa: E501

    def __str__(self):
        return f'{self.id} - {self.email}'

    class Meta:
        verbose_name = 'professor'
        verbose_name_plural = 'professores'
        ordering = ['id']
