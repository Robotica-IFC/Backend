import uuid

from django.db import models

from uploader.models import Image


class Instituicao(models.Model):
    ESTADOS_CHOICES = [
        ('AC', 'Acre'),
        ('AL', 'Alagoas'),
        ('AP', 'Amapá'),
        ('AM', 'Amazonas'),
        ('BA', 'Bahia'),
        ('CE', 'Ceará'),
        ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'),
        ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'),
        ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'),
        ('PA', 'Pará'),
        ('PB', 'Paraíba'),
        ('PR', 'Paraná'),
        ('PE', 'Pernambuco'),
        ('PI', 'Piauí'),
        ('RJ', 'Rio de Janeiro'),
        ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'),
        ('RO', 'Rondônia'),
        ('RR', 'Roraima'),
        ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'),
        ('SE', 'Sergipe'),
        ('TO', 'Tocantins'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=255)
    sigla = models.CharField(max_length=20, null=True, blank=True)
    logo = models.ForeignKey(Image, on_delete=models.SET_NULL, null=True, blank=True)
    cidade = models.CharField(max_length=255)
    estado = models.CharField(max_length=2, choices=ESTADOS_CHOICES)

    def __str__(self):
        return f'{self.nome} - {self.cidade}/{self.estado}'

    def save(self, *args, **kwargs):
        if self.sigla:
            self.sigla = self.sigla.upper()
        super().save(*args, **kwargs)
