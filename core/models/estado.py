from django.db import models


class Estado(models.Model):
    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.nome} ({self.sigla})"

    def save(self, *args, **kwargs):
        if self.sigla:
            self.sigla = self.sigla.upper()
        super().save(*args, **kwargs)
