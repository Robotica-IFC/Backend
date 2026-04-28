import uuid

from django.db import models

from uploader.models import Image

from .instituicao import Instituicao
from .user import User


class Professor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='professor_profile')
    cpf = models.CharField(max_length=11, unique=True)
    descricao = models.TextField(max_length=1000, null=True, blank=True)
    telefone = models.CharField(max_length=15)
    data_nascimento = models.DateField()
    instituicao = models.ForeignKey(Instituicao, on_delete=models.SET_NULL, null=True, blank=True)
    ativo = models.BooleanField(default=True)
    email_verificado = models.BooleanField(default=False)
    imagem_perfil = models.ForeignKey(Image, to_field='attachment_key', related_name='+', on_delete=models.SET_NULL, null=True, blank=True)  # noqa: E501
    is_professor = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.id} - {self.user.email}'

    class Meta:
        verbose_name = 'professor'
        verbose_name_plural = 'professores'
        ordering = ['id']
