import uuid

from django.db import models

from uploader.models import Image
from .user import User


class Aluno(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='aluno_profile')
    descricao = models.TextField(max_length=1000, null=True, blank=True)
    cpf = models.CharField(max_length=11, unique=True)
    telefone = models.CharField(max_length=15)
    data_nascimento = models.DateField()
    ativo = models.BooleanField(default=True)
    email_verificado = models.BooleanField(default=False)
    imagem_perfil = models.ForeignKey(Image, related_name='+', on_delete=models.SET_NULL, null=True, blank=True)  # noqa: E501
    is_aluno = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.id} - {self.user.email}'
