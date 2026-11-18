import uuid

from django.db import models


class CadastroPendente(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True)
    tipo = models.CharField(max_length=10, choices=[('aluno', 'Aluno'), ('professor', 'Professor'), ('usuario', 'Usuário')])
    dados = models.JSONField()
    senha_hash = models.CharField(max_length=128)
    verification_code_hash = models.CharField(max_length=128, blank=True, default='')
    verification_code_created_at = models.DateTimeField(null=True, blank=True)
    verification_attempts = models.PositiveSmallIntegerField(default=0)
    expira_em = models.DateTimeField()
