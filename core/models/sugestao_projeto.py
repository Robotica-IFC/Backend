from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.db import models


class SugestaoProjeto(models.Model):
    titulo = models.CharField(max_length=30)
    descricao = models.TextField(max_length=1000, validators=[MaxLengthValidator(1000)])
    criado_em = models.DateTimeField(auto_now_add=True)
    anonimo = models.BooleanField(default=True)

    equipe = models.ForeignKey(
        'core.Equipe',
        on_delete=models.CASCADE,
        related_name='sugestoes_projeto',
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='sugestoes_projeto',
        null=True,
        blank=True,
    )
    anexos = models.ManyToManyField(
        'uploader.Document',
        related_name='sugestoes_projeto',
        blank=True,
    )

    def __str__(self):
        return f'{self.titulo} - {self.equipe}'

    class Meta:
        verbose_name = 'sugestão de projeto'
        verbose_name_plural = 'sugestões de projeto'
        ordering = ['-criado_em', '-pk']
