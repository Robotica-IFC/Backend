from django.core.exceptions import ValidationError
from django.db import models


class Convite(models.Model):
    class StatusChoices(models.TextChoices):
        PENDENTE = 'P', 'Pendente'
        ACEITO = 'A', 'Aceito'
        NEGADO = 'N', 'Negado'

    convidante = models.ForeignKey(
        'core.Professor',
        related_name='convites_enviados',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    professor = models.ForeignKey(
        'core.Professor',
        related_name='convites_recebidos_professor',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    aluno = models.ForeignKey(
        'core.Aluno',
        related_name='convites_recebidos_aluno',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    equipe = models.ForeignKey(
        'core.Equipe',
        related_name='convites',
        on_delete=models.PROTECT,
    )

    status = models.CharField(
        max_length=1,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDENTE,
    )

    def clean(self):
        super().clean()

        # Garante que existe uma equipe
        if not self.equipe:
            raise ValidationError({'equipe': 'O convite precisa estar associado a uma equipe.'})

        # Garante que o destino é apenas UM (aluno OU professor)
        if bool(self.aluno) == bool(self.professor):
            raise ValidationError('O convite deve ser direcionado para um Aluno ou para um Professor, não ambos.')

        # Garante que o convidante não tente convidar a si mesmo (se for um professor convidando outro professor)
        if self.convidante and self.professor and self.convidante == self.professor:
            raise ValidationError({'professor': 'Você não pode enviar um convite para si mesmo.'})

    def __str__(self):
        destino = self.aluno or self.professor
        return f'Convite de {self.convidante} para {destino} ({self.get_status_display()})'